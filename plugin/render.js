// Rendu du panneau et du titre en PNG (JXA / AppKit)
// usage: osascript -l JavaScript render.js input.json title.png panel.png
function run(argv) {
  ObjC.import('Cocoa');
  var raw = $.NSString.stringWithContentsOfFileEncodingError(argv[0], $.NSUTF8StringEncoding, null);
  var data = JSON.parse(ObjC.unwrap(raw));

  function col(hex, a) {
    var r = parseInt(hex.substr(0, 2), 16) / 255.0;
    var g = parseInt(hex.substr(2, 2), 16) / 255.0;
    var b = parseInt(hex.substr(4, 2), 16) / 255.0;
    return $.NSColor.colorWithCalibratedRedGreenBlueAlpha(r, g, b, a === undefined ? 1 : a);
  }
  function attrs(size, color, weight) {
    var f = (weight === 'bold') ? $.NSFont.boldSystemFontOfSize(size)
          : (weight === 'semi') ? $.NSFont.systemFontOfSizeWeight(size, $.NSFontWeightSemibold)
          : $.NSFont.systemFontOfSize(size);
    var d = $.NSMutableDictionary.alloc.init;
    d.setObjectForKey(f, $.NSFontAttributeName);
    d.setObjectForKey(color, $.NSForegroundColorAttributeName);
    return d;
  }
  function textWidth(s, a) {
    return ObjC.wrap(s).sizeWithAttributes(a).width;
  }
  function beginImage(W, H) {
    var rep = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(
      null, W * 2, H * 2, 8, 4, true, false, $.NSCalibratedRGBColorSpace, 0, 0);
    rep.setSize($.NSMakeSize(W, H));
    $.NSGraphicsContext.saveGraphicsState;
    var ctx = $.NSGraphicsContext.graphicsContextWithBitmapImageRep(rep);
    $.NSGraphicsContext.setCurrentContext(ctx);
    return rep;
  }
  function endImage(rep, outPath) {
    $.NSGraphicsContext.restoreGraphicsState;
    var png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $.NSDictionary.dictionary);
    png.writeToFileAtomically(outPath, true);
  }
  function roundRect(x, y, w, h, r, color) {
    var p = $.NSBezierPath.bezierPathWithRoundedRectXRadiusYRadius($.NSMakeRect(x, y, w, h), r, r);
    color.setFill;
    p.fill;
  }
  function draw(s, x, y, a) {
    ObjC.wrap(s).drawAtPointWithAttributes($.NSMakePoint(x, y), a);
  }

  // ---- Titre (barre de menu) ----
  var TH = 22, tsize = 12.5, gap = 7;
  var parts = data.title;
  var widths = [], total = 0;
  for (var i = 0; i < parts.length; i++) {
    var a = attrs(tsize, col(parts[i].color), 'bold');
    widths.push(textWidth(parts[i].text, a));
    total += widths[i];
  }
  var dotA = attrs(tsize, col('8e8e93'), 'norm');
  var dotW = textWidth(' · ', dotA);
  total += dotW * (parts.length - 1);
  var padX = 9;
  var W0 = Math.ceil(total) + padX * 2;
  var rep = beginImage(W0, TH);
  roundRect(0, 1, W0, TH - 2, (TH - 2) / 2, col('2b2b30'));
  var x = padX, ty = (TH - tsize * 1.32) / 2;
  for (var i = 0; i < parts.length; i++) {
    var a = attrs(tsize, col(parts[i].color), 'bold');
    draw(parts[i].text, x, ty, a);
    x += widths[i];
    if (i < parts.length - 1) { draw(' · ', x, ty, dotA); x += dotW; }
  }
  endImage(rep, argv[1]);

  // ---- Panneau (menu déroulant) ----
  var W = 300, rowH = 58, padX = 16, headH = 26;
  var rows = data.rows;
  var H = headH + rows.length * rowH + 8;
  rep = beginImage(W, H);
  roundRect(0, 0, W, H, 12, col('232327'));
  // en-tête
  draw("LIMITES D'UTILISATION CLAUDE", padX, H - headH + 6, attrs(9.5, col('9a9aa0'), 'semi'));
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i];
    var topY = H - headH - i * rowH; // haut de la rangée
    var c = col(r.color);
    // libellé + pourcentage
    var la = attrs(13, col('f2f2f5'), 'semi');
    draw(r.label, padX, topY - 20, la);
    var pa = attrs(13.5, c, 'bold');
    var pt = r.pct + ' %';
    draw(pt, W - padX - textWidth(pt, pa), topY - 20, pa);
    // barre
    var barY = topY - 32, barW = W - padX * 2, barH = 7;
    roundRect(padX, barY, barW, barH, 3.5, col('4a4a4f'));
    var fw = Math.max(barH, barW * Math.min(100, Math.max(0, r.pct)) / 100);
    roundRect(padX, barY, fw, barH, 3.5, c);
    // réinitialisation
    draw('réinitialisation ' + r.reset, padX, topY - 50, attrs(10.5, col('8e8e93'), 'norm'));
  }
  endImage(rep, argv[2]);
  return 'OK';
}
