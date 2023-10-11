function GetURLParameter(sParam)
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) 
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) 
        {
            return sParameterName[1];
        }
    }
}


$(function() {

    // Add Variant-filtering form
    $("button:last").after('<br><br> \
    <i>(key in variants(row) that you want to hide, separated by comma, no space allowed)</i> <br> \
    <input id="variant_filter" name="variant_filter" size="100%" type="text"><br> \
    <button id="hidevar" type="button">Unshow Variants</button> \
    <button id="showvar" type="button">Show All Variants</button> <br>');


    // ======================================
    // modify libtype filter buttons/info
    // ======================================
    $("button:contains('Hide')").text("ShowOnly");
    $("i:contains('libtypes column to hide')").text("(key in libtypes(column) that you only want to see, separated by comma, no space allowed)");

    // ======================================
    // libtype filter section
    // ======================================
    var all_libtypes = [ "abx2gln", "abx2rtl", "bcmrbc", "bds", "bumps", "cdc", "cdl", "cds", "celfram", "cftest", "cftest2", "cftest3", "circuitsim", "complib", "complibphys", "cv", "cvimpl", "cvrtl", "cvsignoff", "dc", "devprog", "dft", "dftdsm", "dimtable", "docs", "drtest", "dv", "fcflrpln", "fchierflrpln", "fcmw", "fcpnetlist", "fcpwrmod", "fcrba", "fctimemod", "fcv", "fcvnetlist", "firmware", "fishtail", "floorplan", "flrpln", "foundry", "funcrba", "fv", "fvdft", "fvpnr", "fvsyn", "gds", "glnpostpnr", "glnprepnr", "gp", "icc", "intermap", "interrba", "intfc", "ipfloorplan", "ipfram", "ipplace", "ippwrmod", "ipspec", "iptimemod", "ipv", "ipxact", "irem", "kwlimtest", "laymisc", "lint", "mcfd", "mcfl", "mrftemp", "mw", "netlist", "oa", "oasis", "oa_rce", "oa_sim", "optdat", "patrol", "periodictst", "pintable", "pkgde", "pkgee", "pnr", "pnrcts", "pnrintent", "pnrplaced", "portlist", "portmodel", "postpnrscandef", "pt", "pv", "r2g2", "rba", "rcxt", "rdf", "reldoc", "rif", "rlcd", "rtl", "rtl2gds", "rtlcompchk", "rtllec", "rv", "sandbox_project", "scc", "schmisc", "sdc", "sdf", "spyglass", "sta", "stamod", "starvision", "subsysconn", "subsysmw", "syn", "tapeout", "testtesttest", "timemod", "tnodes", "totem", "trackphys", "tv", "tweaker", "upf", "upffc", "upf_netlist", "upf_rtl", "vcs", "vp", "vpd", "vpout", "wild", "yx2gln", "ilib" ];
    $("#hide").click( function() {
        var aaa = $("#libtype_filter").val();
        if (aaa) {
            
            var libtypes = aaa.split(',');
            
            // filter out libtypes that needs to be hidden
            var tobe_hidden = $.grep(all_libtypes, function(value) {
                return $.inArray(value, libtypes) == -1;
            }); // $.grep

            $.each(tobe_hidden, function(index, value) {
                $("."+value).fadeOut();
            }); // $.each
        } // if
    }); // $("#hide")

    $("#show").click( function() {
        $("td").fadeIn();        
        $("th").fadeIn();        
    });

    var libtype_filter = GetURLParameter('libtype_filter');
    $("#libtype_filter").val(libtype_filter);
    $("#show").click();
    $("#hide").click();


    // ======================================
    // Variant filter section
    // ======================================
    $("#hidevar").click( function() {
        var aaa = $("#variant_filter").val();
        if (aaa) {
            var variants = aaa.split(',');
            $("tr").each(function(index, value) {
                if ($.inArray($(this).find("td:first-child").text(), variants) != -1) {
                    $(this).fadeOut();
                }
            }); // $("tr")
        } // if
    });

    $("#showvar").click( function() {
        $("tr").fadeIn();
    });

    var variant_filter = GetURLParameter('variant_filter');
    $("#variant_filter").val(variant_filter);
    $("#showvar").click();
    $("#hidevar").click();


    // ======================================
    // Footer sitemap links
    // ======================================
    
    // Static Page Link
    $("body").append(' | <a id="staticlink" href="#">StaticLink</a>');
    $("#staticlink").click( function() {
        var param = '';
        var varfilt = $("#variant_filter").val();
        var libfilt = $("#libtype_filter").val();
        if (varfilt) {
            param = param + '&variant_filter=' + varfilt;
        }
        if (libfilt) {
            param = param + '&libtype_filter=' + libfilt;
        }
        param = param.replace( /^\&/, "?");

        var url = window.location.href.replace(/[\?#].*|$/, param);
        // window.location.replace( window.location.href.replace(/[\?#].*|$/, param) );
        window.open(url);

    }); // $("#staticlink")

    // Home Link
    $("body").append(' | <a id="home" href="../..">Home</a>');

    //Release Catalog Link
    $("body").append(' | <a id="relcat">Release Catalog</a>');
    var pvc = $("h3").text().replace('- ', '');
    var tmp = pvc.split("/");
    var project = tmp[0];
    tmp = tmp[1].split('@');
    var variant = tmp[0];
    var config = tmp[1];
    if (config.startsWith("REL")) {
        var toi = config.split('__')[0];
        console.log('project:' + project);
        console.log('variant:' + variant);
        console.log('config:' + config);
        console.log('toi:' + toi);
        var url = '';
        if (project == 'i10socfm'  || project == 'Falcon_Mesa') {
            url = 'https://psg-sc-arc.sc.intel.com/p/psg/data/psginfraadm/catalogs/fm/rel/';
        } else {
            url = 'https://sj-arc.altera.com/data/icmrelreader/catalogs/nd-release-catalog/';
        }
        url = url + variant + '/' + toi + '/' + config + '/relnote.html';
        $("#relcat").attr('href', url);
        $("#relcat").attr('target', '_blank');

    } else {
        $("#relcat").css('color', '#aaaaaa');
    }


    // ======================================
    // Make sure design_quality.js javascript 
    // loaded successfully with no errors.
    // ======================================
    console.log('-design_quality.js successfully loaded completely.-');


});

