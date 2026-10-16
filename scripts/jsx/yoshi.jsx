// yoshi.jsx: funções de montagem do Yoshi (ExtendScript + Action Manager), testadas no Photoshop 2026.
// Uso: $.evalFile(".../yoshi.jsx"); Y.doc(1080,1440,"nome"); var g=Y.grupo("FUNDO"); Y.solido("#0B1F3A","COR",g); ...
// Coordenadas sempre em pixels do documento. Grupos: criar de BAIXO para CIMA (cada grupo novo vai para o topo).
var Y = (function () {
  function s(x) { return stringIDToTypeID(x); }
  var D = null;
  function rgb(hex) { var c = new SolidColor(); c.rgb.hexValue = hex.replace("#", ""); return c; }
  function rgbDesc(hex) { var c = rgb(hex), d = new ActionDescriptor(); d.putDouble(s("red"), c.rgb.red); d.putDouble(s("green"), c.rgb.green); d.putDouble(s("blue"), c.rgb.blue); return d; }
  function refAtiva() { var r = new ActionReference(); r.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); return r; }
  function px(v) { return Number(v); }
  function b(l) { var bb = l.bounds; return { x: bb[0].as("px"), y: bb[1].as("px"), w: bb[2].as("px") - bb[0].as("px"), h: bb[3].as("px") - bb[1].as("px") }; }
  function nomeia(l, nome) { if (nome) l.name = nome; return l; }
  function entra(l, g) { if (g) l.move(g, ElementPlacement.PLACEATBEGINNING); D.activeLayer = l; return l; }
  var MODOS = { normal: BlendMode.NORMAL, multiply: BlendMode.MULTIPLY, screen: BlendMode.SCREEN, overlay: BlendMode.OVERLAY,
    softLight: BlendMode.SOFTLIGHT, hardLight: BlendMode.HARDLIGHT, color: BlendMode.COLORBLEND, colorDodge: BlendMode.COLORDODGE,
    linearDodge: BlendMode.LINEARDODGE, linearLight: BlendMode.LINEARLIGHT, lighten: BlendMode.LIGHTEN, darken: BlendMode.DARKEN,
    luminosity: BlendMode.LUMINOSITY, difference: BlendMode.DIFFERENCE, vividLight: BlendMode.VIVIDLIGHT };

  var Y = {};
  Y.doc = function (w, h, nome, fundo) {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS; app.preferences.typeUnits = TypeUnits.PIXELS;
    D = app.documents.add(w, h, 72, nome || "yoshi", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
    D.activeLayer.name = "base";
    return D;
  };
  Y.usar = function (doc) { D = doc || app.activeDocument; app.preferences.rulerUnits = Units.PIXELS; app.preferences.typeUnits = TypeUnits.PIXELS; return D; };
  Y.grupo = function (nome, pai) {
    var g = D.layerSets.add(); g.name = nome;
    if (pai) g.move(pai, ElementPlacement.PLACEATBEGINNING); else g.move(D, ElementPlacement.PLACEATBEGINNING);
    return g;
  };
  Y.misturar = function (l, modo, opacidade) { if (modo) l.blendMode = MODOS[modo]; if (opacidade !== undefined) l.opacity = opacidade; return l; };

  // ---------- cor ----------
  Y.solido = function (hex, nome, g, modo, op) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), f = new ActionDescriptor(); f.putObject(s("color"), s("RGBColor"), rgbDesc(hex));
    u.putObject(s("type"), s("solidColorLayer"), f); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome); Y.misturar(l, modo, op); return entra(l, g);
  };
  // paradas: [["#000000",0,100],["#000000",100,0]] (cor, posição %, opacidade %). angulo: 90 = de baixo para cima.
  Y.degrade = function (paradas, angulo, nome, g, modo, op) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), gd = new ActionDescriptor();
    gd.putUnitDouble(s("angle"), s("angleUnit"), angulo === undefined ? 90 : angulo); gd.putEnumerated(s("type"), s("gradientType"), s("linear"));
    var gr = new ActionDescriptor(); gr.putString(s("name"), "yoshi"); gr.putEnumerated(s("gradientForm"), s("gradientForm"), s("customStops")); gr.putDouble(s("interfaceIconFrameDimmed"), 4096);
    var cl = new ActionList(), tl = new ActionList();
    for (var i = 0; i < paradas.length; i++) {
      var p = paradas[i], loc = Math.round(p[1] / 100 * 4096);
      var c = new ActionDescriptor(); c.putObject(s("color"), s("RGBColor"), rgbDesc(p[0])); c.putEnumerated(s("type"), s("colorStopType"), s("userStop"));
      c.putInteger(s("location"), loc); c.putInteger(s("midpoint"), 50); cl.putObject(s("colorStop"), c);
      var t = new ActionDescriptor(); t.putUnitDouble(s("opacity"), s("percentUnit"), p.length > 2 ? p[2] : 100); t.putInteger(s("location"), loc); t.putInteger(s("midpoint"), 50); tl.putObject(s("transferSpec"), t);
    }
    gr.putList(s("colors"), cl); gr.putList(s("transparency"), tl); gd.putObject(s("gradient"), s("gradientClassEvent"), gr);
    u.putObject(s("type"), s("gradientLayer"), gd); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome); Y.misturar(l, modo, op); return entra(l, g);
  };

  // ---------- imagem ----------
  // caixa {x,y,w,h}; ajuste: "cobrir" (preenche a caixa, corta), "conter" (cabe inteira), "largura", "altura".
  // alinhar: "centro" (padrão), "base" (encosta embaixo), "topo".
  Y.colocar = function (caminho, nome, g, caixa, ajuste, alinhar) {
    var a = new ActionDescriptor(); a.putPath(s("null"), new File(caminho));
    a.putEnumerated(s("freeTransformCenterState"), s("quadCenterState"), s("QCSAverage")); executeAction(s("placeEvent"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome);
    if (caixa) Y.encaixar(l, caixa, ajuste || "cobrir", alinhar || "centro");
    return entra(l, g);
  };
  Y.encaixar = function (l, c, ajuste, alinhar) {
    var bb = b(l), sx = c.w / bb.w, sy = c.h / bb.h, e;
    if (ajuste === "conter") e = Math.min(sx, sy); else if (ajuste === "largura") e = sx; else if (ajuste === "altura") e = sy; else e = Math.max(sx, sy);
    l.resize(e * 100, e * 100, AnchorPosition.MIDDLECENTER);
    bb = b(l);
    var dx = c.x + (c.w - bb.w) / 2 - bb.x, dy;
    if (alinhar === "base") dy = c.y + c.h - bb.h - bb.y; else if (alinhar === "topo") dy = c.y - bb.y; else dy = c.y + (c.h - bb.h) / 2 - bb.y;
    l.translate(dx, dy); return l;
  };
  // Recorta a pessoa/objeto principal (Selecionar assunto, IA local) e cria máscara na camada.
  Y.recortar = function (l) {
    D.activeLayer = l; var a = new ActionDescriptor(); a.putBoolean(s("sampleAllLayers"), false); executeAction(s("autoCutout"), a, DialogModes.NO);
    var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask"));
    m.putReference(s("at"), r); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealSelection")); executeAction(s("make"), m, DialogModes.NO);
    D.selection.deselect(); return l;
  };
  // "Pessoa na frente do título": duplica a foto já recortada para outro grupo (acima do texto).
  Y.duplicarPara = function (l, nome, g) { var c = l.duplicate(); c.name = nome; return entra(c, g); };
  // Esconde a parte de baixo de uma camada com máscara de degradê (para a foto "sumir" no fundo). de/ate em px de y.
  Y.sumirEmbaixo = function (l, yInicio, yFim) {
    D.activeLayer = l;
    var temMascara = false; try { var r0 = new ActionReference(); r0.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); temMascara = executeActionGet(r0).getBoolean(s("hasUserMask")); } catch (e) {}
    if (!temMascara) { var m = new ActionDescriptor(); m.putClass(s("new"), s("channel")); var r = new ActionReference(); r.putEnumerated(s("channel"), s("channel"), s("mask")); m.putReference(s("at"), r); m.putEnumerated(s("using"), s("userMaskEnabled"), s("revealAll")); executeAction(s("make"), m, DialogModes.NO); }
    // seleciona o canal da máscara e pinta um degradê branco->preto multiplicando (intersecção) via seleção com difusão
    var sel = [[0, yFim], [D.width.as("px"), yFim], [D.width.as("px"), D.height.as("px")], [0, D.height.as("px")]];
    D.selection.select(sel, SelectionType.REPLACE, (yFim - yInicio) / 2, false);
    var rc = new ActionReference(); rc.putEnumerated(s("channel"), s("channel"), s("mask")); var sc = new ActionDescriptor(); sc.putReference(s("null"), rc); sc.putBoolean(s("makeVisible"), false); executeAction(s("select"), sc, DialogModes.NO);
    D.selection.fill(rgb("#000000")); D.selection.deselect();
    var rl = new ActionReference(); rl.putEnumerated(s("channel"), s("channel"), s("RGB")); var sl = new ActionDescriptor(); sl.putReference(s("null"), rl); executeAction(s("select"), sl, DialogModes.NO);
    return l;
  };

  // ---------- texto ----------
  // o: {txt, fonte, px, cor, x, y, ancora:"tl|tc|tr|bl|bc", tracking, entrelinha, caixa:{w,h}, alinh:"esq|centro|dir", caps,
  //     faixas:[{de,ate,fonte,px,cor}]}  (faixas = trechos com estilo diferente dentro da mesma camada)
  Y.texto = function (o, g) {
    var l = D.artLayers.add(); l.kind = LayerKind.TEXT; var ti = l.textItem;
    if (o.caixa) { ti.kind = TextType.PARAGRAPHTEXT; ti.width = o.caixa.w; ti.height = o.caixa.h; }
    ti.contents = o.txt.replace(/\n/g, "\r"); ti.font = o.fonte; ti.size = o.px; ti.color = rgb(o.cor || "#FFFFFF");
    ti.justification = o.alinh === "centro" ? Justification.CENTER : (o.alinh === "dir" ? Justification.RIGHT : Justification.LEFT);
    if (o.tracking !== undefined) ti.tracking = o.tracking;
    if (o.entrelinha) { ti.useAutoLeading = false; ti.leading = o.entrelinha; }
    if (o.caps) ti.capitalization = TextCase.ALLCAPS;
    ti.antiAliasMethod = AntiAlias.SMOOTH;
    nomeia(l, o.nome || o.txt.split("\n")[0].substr(0, 30));
    if (o.faixas) Y.faixas(l, o.faixas);
    if (o.caixa) { ti.position = [o.x, o.y]; }
    else Y.ancorar(l, o.x, o.y, o.ancora || "tl");
    return entra(l, g);
  };
  Y.ancorar = function (l, x, y, anc) {
    var bb = b(l), tx = x - bb.x, ty = y - bb.y;
    if (anc.charAt(1) === "c") tx = x - bb.w / 2 - bb.x; if (anc.charAt(1) === "r") tx = x - bb.w - bb.x;
    if (anc.charAt(0) === "b") ty = y - bb.h - bb.y; if (anc.charAt(0) === "m") ty = y - bb.h / 2 - bb.y;
    l.translate(tx, ty); return l;
  };
  Y.faixas = function (l, fx) {
    D.activeLayer = l;
    var tk = executeActionGet(refAtiva()).getObjectValue(s("textKey")), base = tk.getList(s("textStyleRange")).getObjectValue(0).getObjectValue(s("textStyle"));
    var total = l.textItem.contents.length, nl = new ActionList(), marc = [], i, k;
    // preenche os buracos entre faixas com o estilo base
    var lista = [], pos = 0; fx.sort(function (a, c) { return a.de - c.de; });
    for (i = 0; i < fx.length; i++) { if (fx[i].de > pos) lista.push({ de: pos, ate: fx[i].de }); lista.push(fx[i]); pos = fx[i].ate; }
    if (pos < total) lista.push({ de: pos, ate: total });
    for (i = 0; i < lista.length; i++) {
      var f = lista[i], r = new ActionDescriptor(); r.putInteger(s("from"), f.de); r.putInteger(s("to"), f.ate);
      var st = new ActionDescriptor();
      for (k = 0; k < base.count; k++) { var key = base.getKey(k); try { var t = base.getType(key);
        if (t == DescValueType.STRINGTYPE) st.putString(key, base.getString(key)); else if (t == DescValueType.UNITDOUBLE) st.putUnitDouble(key, base.getUnitDoubleType(key), base.getUnitDoubleValue(key));
        else if (t == DescValueType.DOUBLETYPE) st.putDouble(key, base.getDouble(key)); else if (t == DescValueType.INTEGERTYPE) st.putInteger(key, base.getInteger(key));
        else if (t == DescValueType.BOOLEANTYPE) st.putBoolean(key, base.getBoolean(key)); else if (t == DescValueType.ENUMERATEDTYPE) st.putEnumerated(key, base.getEnumerationType(key), base.getEnumerationValue(key));
        else if (t == DescValueType.OBJECTTYPE) st.putObject(key, base.getObjectType(key), base.getObjectValue(key)); } catch (e) {} }
      if (f.fonte) { st.putString(s("fontPostScriptName"), f.fonte); }
      if (f.px) { st.putUnitDouble(s("size"), s("pixelsUnit"), f.px); }
      if (f.cor) st.putObject(s("color"), s("RGBColor"), rgbDesc(f.cor));
      if (f.tracking !== undefined) st.putInteger(s("tracking"), f.tracking);
      r.putObject(s("textStyle"), s("textStyle"), st); nl.putObject(s("textStyleRange"), r);
    }
    tk.putList(s("textStyleRange"), nl);
    var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); a.putObject(s("to"), s("textLayer"), tk); executeAction(s("set"), a, DialogModes.NO);
    return l;
  };

  // ---------- formas ----------
  // o: {x,y,w,h,cor,raio,nome, contorno:{px,cor}, so_contorno:true}
  Y.retangulo = function (o, g) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), f = new ActionDescriptor(); f.putObject(s("color"), s("RGBColor"), rgbDesc(o.cor || "#FFFFFF")); u.putObject(s("type"), s("solidColorLayer"), f);
    var sh = new ActionDescriptor(); sh.putInteger(s("unitValueQuadVersion"), 1);
    sh.putUnitDouble(s("top"), s("pixelsUnit"), o.y); sh.putUnitDouble(s("left"), s("pixelsUnit"), o.x); sh.putUnitDouble(s("bottom"), s("pixelsUnit"), o.y + o.h); sh.putUnitDouble(s("right"), s("pixelsUnit"), o.x + o.w);
    var rr = o.raio || 0; sh.putUnitDouble(s("topRight"), s("pixelsUnit"), rr); sh.putUnitDouble(s("topLeft"), s("pixelsUnit"), rr); sh.putUnitDouble(s("bottomLeft"), s("pixelsUnit"), rr); sh.putUnitDouble(s("bottomRight"), s("pixelsUnit"), rr);
    u.putObject(s("shape"), s("rectangle"), sh); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, o.nome || "RETANGULO");
    if (o.contorno) Y.efeitos(l, { traco: { px: o.contorno.px, cor: o.contorno.cor, posicao: "inside" } });
    if (o.so_contorno) l.fillOpacity = 0;
    if (o.opacidade !== undefined) l.opacity = o.opacidade;
    return entra(l, g);
  };
  Y.elipse = function (o, g) {
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("contentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), f = new ActionDescriptor(); f.putObject(s("color"), s("RGBColor"), rgbDesc(o.cor || "#FFFFFF")); u.putObject(s("type"), s("solidColorLayer"), f);
    var sh = new ActionDescriptor(); sh.putUnitDouble(s("top"), s("pixelsUnit"), o.y); sh.putUnitDouble(s("left"), s("pixelsUnit"), o.x); sh.putUnitDouble(s("bottom"), s("pixelsUnit"), o.y + o.h); sh.putUnitDouble(s("right"), s("pixelsUnit"), o.x + o.w);
    u.putObject(s("shape"), s("ellipse"), sh); a.putObject(s("using"), s("contentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, o.nome || "ELIPSE");
    if (o.contorno) Y.efeitos(l, { traco: { px: o.contorno.px, cor: o.contorno.cor, posicao: "inside" } });
    if (o.so_contorno) l.fillOpacity = 0;
    return entra(l, g);
  };

  // ---------- estilos de camada ----------
  // fx: {sombra:{cor,op,dist,desfoque,angulo}, traco:{px,cor,posicao:"outside|inside|center"}, cor:{cor,op}, degrade:{paradas,angulo}, brilho:{cor,op,tam}}
  Y.efeitos = function (l, fx) {
    D.activeLayer = l;
    var a = new ActionDescriptor(), r = new ActionReference(); r.putProperty(s("property"), s("layerEffects")); r.putEnumerated(s("layer"), s("ordinal"), s("targetEnum")); a.putReference(s("null"), r);
    var e = new ActionDescriptor(); e.putUnitDouble(s("scale"), s("percentUnit"), 100);
    if (fx.sombra) { var o = fx.sombra, d = new ActionDescriptor(); d.putBoolean(s("enabled"), true); d.putEnumerated(s("mode"), s("blendMode"), s("multiply"));
      d.putObject(s("color"), s("RGBColor"), rgbDesc(o.cor || "#000000")); d.putUnitDouble(s("opacity"), s("percentUnit"), o.op || 50);
      d.putUnitDouble(s("distance"), s("pixelsUnit"), o.dist || 10); d.putUnitDouble(s("blur"), s("pixelsUnit"), o.desfoque || 30); d.putUnitDouble(s("localLightingAngle"), s("angleUnit"), o.angulo || 90); d.putBoolean(s("useGlobalAngle"), false);
      e.putObject(s("dropShadow"), s("dropShadow"), d); }
    if (fx.traco) { var t = fx.traco, st = new ActionDescriptor(); st.putBoolean(s("enabled"), true);
      st.putEnumerated(s("style"), s("frameStyle"), s(t.posicao === "inside" ? "insetFrame" : (t.posicao === "center" ? "centeredFrame" : "outsetFrame")));
      st.putEnumerated(s("paintType"), s("frameFill"), s("solidColor")); st.putEnumerated(s("mode"), s("blendMode"), s("normal"));
      st.putUnitDouble(s("opacity"), s("percentUnit"), 100); st.putUnitDouble(s("size"), s("pixelsUnit"), t.px || 2); st.putObject(s("color"), s("RGBColor"), rgbDesc(t.cor || "#FFFFFF"));
      e.putObject(s("frameFX"), s("frameFX"), st); }
    if (fx.cor) { var c = new ActionDescriptor(); c.putBoolean(s("enabled"), true); c.putEnumerated(s("mode"), s("blendMode"), s("normal"));
      c.putObject(s("color"), s("RGBColor"), rgbDesc(fx.cor.cor)); c.putUnitDouble(s("opacity"), s("percentUnit"), fx.cor.op || 100); e.putObject(s("solidFill"), s("solidFill"), c); }
    if (fx.brilho) { var gl = new ActionDescriptor(); gl.putBoolean(s("enabled"), true); gl.putEnumerated(s("mode"), s("blendMode"), s("screen"));
      gl.putObject(s("color"), s("RGBColor"), rgbDesc(fx.brilho.cor)); gl.putUnitDouble(s("opacity"), s("percentUnit"), fx.brilho.op || 60);
      gl.putUnitDouble(s("blur"), s("pixelsUnit"), fx.brilho.tam || 40); gl.putUnitDouble(s("chokeMatte"), s("percentUnit"), 0); e.putObject(s("outerGlow"), s("outerGlow"), gl); }
    a.putObject(s("to"), s("layerEffects"), e); executeAction(s("set"), a, DialogModes.NO); return l;
  };

  // ---------- acabamento ----------
  Y.grao = function (g, quantidade, opacidade) {
    var l = D.artLayers.add(); l.name = "GRANULACAO"; D.selection.selectAll(); D.selection.fill(rgb("#808080")); D.selection.deselect();
    l.applyAddNoise(quantidade || 12, NoiseDistribution.GAUSSIAN, true); l.blendMode = BlendMode.OVERLAY; l.opacity = opacidade === undefined ? 35 : opacidade;
    return entra(l, g);
  };
  Y.curvas = function (pontos, nome, g, op) { // pontos [[0,0],[64,50],[192,205],[255,255]] (canal composto)
    var a = new ActionDescriptor(), r = new ActionReference(); r.putClass(s("adjustmentLayer")); a.putReference(s("null"), r);
    var u = new ActionDescriptor(), cv = new ActionDescriptor(); cv.putEnumerated(s("presetKind"), s("presetKindType"), s("presetKindCustom"));
    var lst = new ActionList(), ch = new ActionDescriptor(), rc = new ActionReference(); rc.putEnumerated(s("channel"), s("channel"), s("composite")); ch.putReference(s("channel"), rc);
    var pl = new ActionList(); for (var i = 0; i < pontos.length; i++) { var p = new ActionDescriptor(); p.putDouble(s("horizontal"), pontos[i][0]); p.putDouble(s("vertical"), pontos[i][1]); pl.putObject(s("paint"), p); }
    ch.putList(s("curve"), pl); lst.putObject(s("curvesAdjustment"), ch); cv.putList(s("adjustment"), lst);
    u.putObject(s("type"), s("curves"), cv); a.putObject(s("using"), s("adjustmentLayer"), u); executeAction(s("make"), a, DialogModes.NO);
    var l = D.activeLayer; nomeia(l, nome || "CURVAS"); if (op !== undefined) l.opacity = op; return entra(l, g);
  };
  Y.recorte = function (l) { D.activeLayer = l; var a = new ActionDescriptor(); a.putReference(s("null"), refAtiva()); executeAction(s("groupEvent"), a, DialogModes.NO); return l; };

  // ---------- saída ----------
  Y.salvar = function (psd, png) {
    try { D.artLayers.getByName("base").remove(); } catch (e) {}
    if (psd) { var o = new PhotoshopSaveOptions(); o.layers = true; o.embedColorProfile = true; D.saveAs(new File(psd), o, false); }
    if (png) { D.saveAs(new File(png), new PNGSaveOptions(), true); }
    return psd || png;
  };
  // Carrossel panorâmico: exporta n fatias de largura w (PNG) a partir do documento inteiro. prefixo + "-01.png"...
  Y.fatiar = function (prefixo, n, w) {
    var orig = D, h = D.height.as("px");
    for (var i = 0; i < n; i++) {
      var c = orig.duplicate("fatia", true); // achatada
      c.crop([i * w, 0, (i + 1) * w, h]);
      c.saveAs(new File(prefixo + "-" + (i < 9 ? "0" : "") + (i + 1) + ".png"), new PNGSaveOptions(), true);
      c.close(SaveOptions.DONOTSAVECHANGES);
    }
    app.activeDocument = orig; D = orig; return n;
  };
  Y.bounds = function (l) { var bb = b(l); return bb.x + "," + bb.y + "," + bb.w + "," + bb.h; };
  Y.D = function () { return D; };
  return Y;
})();
