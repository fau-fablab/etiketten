<?php

/*
====================================================================


Etiketten-Templatesystem (C) Max Gaukler 2012
Public Domain / zur uneingeschränkten Verwendung freigegeben, keine Garantie für Funktionsfähigkeit

*/

/**
 * Inserts some HTML at the top of the document. This is needet for the FAU FabLab website style
 */
function insert_html_lines_top() {
	echo '<!DOCTYPE html>
	<html>
  <head>
	    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
	    <title>Etikettendruck | FAU FabLab</title>
	    <link type="text/css" rel="stylesheet" media="all" href="https://user.fablab.fau.de/~ev80uhys/web/faufablab-light.css" />
	    <link rel="shortcut icon" href="https://fablab.fau.de/sites/fablab.fau.de/files/fablab_favicon_1.ico" type="image/x-icon">
  </head>

	  <body>

         <div id="header" class="header">
             <div id="logo" class="logo">
                 <a href="https://fablab.fau.de">
                     <img src="https://fablab.fau.de/sites/fablab.fau.de/files/acquia_marina_logo.png" alt="Startseite">
                 </a>
             </div>

             <div id="fork-on-github" style="position: fixed; top: 0; right: 0; border: 0;">
                 <a href="https://github.com/fau-fablab/etiketten">
                     <img src="https://camo.githubusercontent.com/52760788cde945287fbb584134c4cbc2bc36f904/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f77686974655f6666666666662e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_white_ffffff.png">
                 </a>
             </div>
         </div>

        <div id="top" class="top">
        </div>


        <div id="content" class="content">
            <h1>Etiketten</h1>';
}

/**
 * Inserts some HTML at the bottom of the document. This is needet for the FAU FabLab website style
 */
function insert_html_lines_bottom() {
	echo '</div>
	</div>


	<div id="bottom" class="bottom">
	</div>

    </body>
</html>';
}

/**
 * Expands item ranges (123-125 -> 123,124,125)
 * @param $items array of items and item ranges
 * @return array of expanded items
 */
function expand_array_ranges($items) {
	$items_expanded=array();
	foreach ($items as $i) {
		$stroke_position=strpos($i,"-");
		if ($stroke_position===FALSE) {
            // normal entry, no range
            $items_expanded[] = $i;
        } elseif (strpos($i,'po')!==FALSE) {
            // purchase order
            $items_expanded = array_merge($items_expanded, explode('-', $i));
		} else {
			// number range
			$start = intval(substr($i,0,$stroke_position));
			$end=intval(substr($i,$stroke_position+1));
			for ($n=$start; $n <= $end; $n++) {
				$items_expanded[]=(string) $n;
			}
		}
	}
	return $items_expanded;
}

/**
 * generates labels in one pdf-file (uses svgtemplate.py)
 * @param $items array of product ids and purchase orders
 * @param $print (True|False) if the generated pdf should be printed directly
 * @param $start_position (???)
 * @return string the filename of the generated pdf (relative)
 */
function generate_pdf_small($items,$print,$start_position) {
	// <editor-fold desc="Inkscape braucht ein schreibbares HOME">
	putenv("HOME=".getcwd()."/temp");
	if (file_exists("./temp/output-etikettenpapier.pdf")) {
		unlink("./temp/output-etikettenpapier.pdf");
	}
	#chdir("./SVG");
    # </editor-fold>
	$items_str="";
	foreach($items as $item) {
		$items_str .= " " . $item;
	}

	# if (preg_match('/^[0-9]*$/',$items_str)===1) {
    if (preg_match('/^( \d{1,4}| po\d{5}){1,50}$/', $items_str)===1) {
        // regex explanation: matches ether a number up to 4 digits (-> for product ids)
        // or a string with 'po' and a 5 digits number (-> for purchase orders)
        // Such combinations are allowed up to 50 times and must begin at the start of the string and end at the end.
        // Problems: works only for lower case (strtolower is used when using $_POST['etiketten']) expressions
        // and only with leading ' ' (done in foreach above).
        for ($i = 0; $i < $start_position; $i++) {
            $items_str = "None " . $items_str;
        }

        system("./svgtemplate.py " . $items_str);
        #chdir("../");
        if ($print) {
            system("lpr -P Zebra-EPL2-Label ./temp/output-etikettenpapier.pdf");
        }
        return "./temp/output-etikettenpapier.pdf";
    } else {
        die_friendly("illegal character in ID");
    }
}

/**
 * Displays an error message and then it dies
 * @param $message string error message to display
 */
function die_friendly($message) {
    insert_html_lines_top();
    echo '<div class="error"><p>Es trat ein Fehler auf:</p><p>' . $message . '</p></div></br>
			<form action="elektro-etiketten.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form><br /><p>R.I.P.</p>';
    insert_html_lines_bottom();
    die();
}


if (empty($_POST["etiketten"])) {
    # <editor-fold desc="show input form">
	insert_html_lines_top();

	echo '<form action="elektro-etiketten.php" method="post" style="text-align: center"><b>Artikel- (ERP: <code>interne Referenz</code>) oder Bestellungsnummern:</b> <br />
        <input name="etiketten" type="text" style="width:80%;margin:1em;text-align: center;font-size: large" placeholder="z.B.  541 123 9001 PO12345" autocomplete="off" autofocus> <br />
		<input type="submit" name="print" value="Drucken">    <input type="submit" name="pdf" value="anzeigen" style="font-weight:normal; background:linear-gradient(to bottom, #B3C6D3 0%, #95A8B4 100%);"> 
		<!-- BASTELEI: Format-Auswahl deaktiviert, hidden input der fest auf small und 0 bereits verbraucht stellt -->
		<input type="hidden" name="type" value="small"/>
		<input type="hidden" name="startposition" value="0"/>
		</form>

	    <p>Zum Drucken weiße Papier-Etiketten in den Etikettendrucker einlegen — nicht die silbernen!</p>
	    <p>Probleme bitte an die <a href="mailto:fablab-aktive@fablab.fau.de">Mailingliste</a> oder auf <a href="https://github.com/fau-fablab/etiketten">GitHub</a> melden.</p>

        <h3 style="margin-top:2cm">Details:</h3>
		<p>
	        <ul><li>Artikelnummern werden im ERP bei <code>interne Referenz</code> als vierstellige Zahl (mit führenden Nullen) eingetragen, z.B. <code>0154</code>. Die führenden Nullen können hier weggelassen werden.</li>
	        <li>Bestellungsnummern werdem im ERP unter <code>Einkauf / Angebote od. Bestellungen</code> in der &Uuml;berschrift angezeigt. Sie bestehen aus dem Pr&auml;fix <code>PO</code> und einer 5 stelligen Zahl (mit führenden Nullen).</li>
	        <li>Mehrere Artikelnummern und Bestellungsnummern durch Leerzeichen oder Komma trennen. Bereiche von Artikelnummern gehen auch: <code>100-123</code></li>
            <li>Der aufgedruckte Ort wird als Lagerort des Artikels oder der Kategorie eingetragen. (Kategorien vererben den Ort nicht an Unterkategorien!)</li>
	        <li>Die Artikelnummern können in <a href="https://eichhörnchen.fablab.fau.de">OpenERP</a> oder in der <a href="https://user.fablab.fau.de/~buildserver/pricelist/output/">Teile Übersicht</a> nachgeschaut werden.</li>
	    </ul></p>

		<!-- <ul><li><b>Bitte angeben:</b> Format:
		<select name="type" size="1">
		  <option value="small">klein (6x3cm), Selbstklebe-Etikettenpapier (f&uuml;r Schubladenmagazine)</option>
		  <option value="large">groß (ca 8x10cm), normales Papier (f&uuml;r Elektronik-T&uuml;tchen)</option>
		</select></br></br>
		</li>
		<li>
		<b>Bitte angeben:</b> Wie viele Etiketten auf diesem Bogen wurden bereits verbraucht?
		<input type="text" value="0" name="startposition"></br></br>
		</li></ul> -->

		';

    insert_html_lines_bottom();
    # </editor-fold>
} else {
    # <editor-fold desc="evaluate POST input">
	//print_r($_POST);

    # <editor-fold desc="explode input to array of product ids and purchase order ids">
    # simplify: separator: ',' and to lower. Watch out: ' - ' -> ',-,'
    $input_ids = strtolower(str_replace(array(",", ";", "|", " "), ",", $_POST["etiketten"]));
    # simplify: ',,,,' -> ','
    while(strpos($input_ids, ',,')) { $input_ids = str_replace(",,", ",", $input_ids); }
    # simplify: ',123,-,125' -> '123-125'
    $input_ids = trim(str_replace(array(",-", "-,"), "-", $input_ids), ',');
    # creates an array containing the ids and id ranges
	$items=array_filter(explode(",",$input_ids));
	$items=expand_array_ranges($items);
    # </editor-fold>

	if (isset($_POST["type"])) {
        $print = isset($_POST["print"]);

        $output = "";
        if ($_POST["type"] == "large") {
            die_friendly("zur Zeit deaktiviert");
            # $output=erzeuge_pdf($items, $print);
        } else if ($_POST["type"] == "small") {
            // kleine Etiketten für selbstklebendes Papier
            $output = generate_pdf_small($items, $print, $_POST["startposition"]);
        } else {
            die_friendly("What have you done?!?");
        }

        if ($print) {
            insert_html_lines_top();

            echo '<p><b>Etiketten werden ausgedruckt.</b></p></br>
			<form action="elektro-etiketten.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form>';

            insert_html_lines_bottom();
        } else {
            header('Content-type: application/pdf');
            header('Content-Disposition: attachment; filename="downloaded.pdf"');
            readfile($output);
        }
	} else {
        die_friendly("What have you done?!?");
	}
    # </editor-fold>
}
