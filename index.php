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
            # <editor-fold desc="get repeat statement">
            $pre = "";
            if( is_numeric(explode('x', substr($i, 0, 3), 2)[0]) ) {
                # the item starts with a repeat statement (btw: $i is already strtolower)
                $pre = intval(explode('x', substr($i, 0, 3), 2)[0]) . 'x';
                $pos = strpos($i, 'x');
                $i = substr($i, $pos + 1);
            }
            # </editor-fold>
            $stroke_position=strpos($i,"-");
			$start = intval(substr($i,0,$stroke_position));
			$end=intval(substr($i,$stroke_position+1));
			for ($n=$start; $n <= $end; $n++) {
				$items_expanded[] = $pre . (string)$n;
			}
		}
	}
	return $items_expanded;
}

/**
 * generates labels in one pdf-file (uses svgtemplate.py)
 * @param $items array of product ids and purchase orders
 * @param $print (True|False) if the generated pdf should be printed directly
 * @param $start_position int Always 0 for label printers that can print each label separately. For multiple labels on one page (e.g. with 16-label sheets on a normal printer), skip the first N places (because they were already used)
 * @return string the filename of the generated pdf (relative)
 */
function generate_pdf_small($items, $print, $start_position) {
	// Inkscape braucht ein schreibbares HOME
	putenv("HOME=".getcwd()."/temp");
    
	if (file_exists("./temp/output-etikettenpapier.pdf")) {
		unlink("./temp/output-etikettenpapier.pdf");
	}
	#chdir("./SVG");
	$items_str="";
	foreach($items as $item) {
		$items_str .= " " . $item;
	}

	# if (preg_match('/^[0-9]*$/',$items_str)===1) {
    # if (preg_match('/^( \d{1,4}| po\d{5}){1,50}$/', $items_str)===1) {
    if (preg_match('/^( (\d{1,2}x)?(\d{1,4}|po\d{5})){1,50}$/', $items_str)===1) {
        // regex explanation: matches ether a number up to 4 digits (-> for product ids)
        // or a string with 'po' and a 5 digits number (-> for purchase orders)
        // in front of it there might be a up to two digit number with an 'x' (12x1337 -> "12 times 1337")
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
        die_friendly("Ungültige Eingabe oder unerlaubtes Zeichen");
        return "";
    }
}

/**
 * Print plaintext labels
 * @param $oneLabel True: make one big label with multiple lines
 *                  False: multiple labels, one per text line
 */
function print_text_label($text,$oneLabel) {
    // based on example code from http://php.net/manual/en/function.proc-open.php
    $descriptorspec = array(
       0 => array("pipe", "r"),  // stdin
       1 => array("pipe", "w"),  // stdout
       2 => array("pipe", "w") // stderr
    );

    $option="--multiple-labels";
    if ($oneLabel) {
        $option="--one-label";
    }
    $process = proc_open('./textlabel.py --print '.$option, $descriptorspec, $pipes);

    if (!is_resource($process)) {
        die_friendly("failed to start textlabel.py");
    }
    
    
    // write to stdin
    fwrite($pipes[0], $text);
    fclose($pipes[0]);
    
    $stdout=stream_get_contents($pipes[1]);
    fclose($pipes[1]);
    
    $stderr=stream_get_contents($pipes[2]);
    fclose($pipes[2]);
    
    $return_value = proc_close($process);
    if ($return_value != 0) {
        die_friendly("textlabel.py returned error $return_value: \n".$stdout."\n".$stderr);
    }
}

/**
 * Displays an error message and then it dies
 * @param $message string error message to display
 */
function die_friendly($message) {
    insert_html_lines_top();
    echo '<div class="error"><p>Es trat ein Fehler auf:</p><p>' . $message . '</p></div></br>
			<form action="index.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form><br /><p>R.I.P.</p>';
    insert_html_lines_bottom();
    die();
}


if (empty($_POST["etiketten"])) {
    # <editor-fold desc="show input form">
	insert_html_lines_top();

	echo '<h2>Produkt-Etiketten</h2><form action="index.php" method="post" style="text-align: center"><b>Artikelnummern (ERP: „interne Referenz“) oder Bestellungsnummern:</b>    
        <input name="etiketten" type="text" style="width:80%;margin:1em;text-align: center;font-size: large" placeholder="z.B.  541 123 9001 PO12345" autocomplete="off" autofocus> <br />
		<button type="submit" name="action" value="print">direkt Drucken</button>
		<!--<button type="submit" name="action" value="select">Anzahl w&auml;hlen</button>-->
		<!--<button type="submit" name="action" value="preview">Vorschau anzeigen</button>-->
		<!-- BASTELEI: Format-Auswahl deaktiviert, hidden input der fest auf small und 0 bereits verbraucht stellt -->
		<input type="hidden" name="type" value="small"/>
		<input type="hidden" name="startposition" value="0"/>
		</form>
<hr/>
        <h2>Freitext-Eingabe</h2>
        <form action="index.php" method="post" style="text-align: center"><b>Text:</b> <br />
        <textarea name="etiketten" style="font-family:auto; width:80%;margin:1em;text-align: center;font-size: large; height:5em;" placeholder="Hier Text eingeben
Auch mehrzeilig

" autocomplete="off"></textarea><br />
Anzahl: <input type="number" name="number" value="1" label="Anzahl"/> Stück<br/>
		<button type="submit" name="textlabel_type" value="multiple">Drucken: mehrere Etiketten<br/> eines pro Zeile</button>
        <button type="submit" name="textlabel_type" value="one">Drucken: alles auf ein Etikett</button>
		<input type="hidden" name="type" value="text"/>
        <input type="hidden" name="action" value="print"/>
        
		<input type="hidden" name="startposition" value="0"/>
		</form>
        
        <hr/>
        
	    <p>Zum Drucken weiße Papier-Etiketten in den Etikettendrucker einlegen — nicht die silbernen!</p>
	    <p>Probleme bitte an die <a href="mailto:fablab-aktive@fablab.fau.de">Mailingliste</a> oder auf <a href="https://github.com/fau-fablab/etiketten">GitHub</a> melden.</p>

        
        <h3 style="margin-top:2cm">Details:</h3>
		<p>
	        <ul><li>Artikelnummern werden im ERP bei <code>interne Referenz</code> als vierstellige Zahl (mit führenden Nullen) eingetragen, z.B. <code>0154</code>. Die führenden Nullen können hier weggelassen werden.</li>
	        <li>Bestellungsnummern werdem im ERP unter <code>Einkauf / Angebote od. Bestellungen</code> in der &Uuml;berschrift angezeigt. Sie bestehen aus dem Pr&auml;fix <code>PO</code> und einer 5 stelligen Zahl (mit führenden Nullen).</li>
	        <li>Mehrere Artikelnummern und Bestellungsnummern durch Leerzeichen oder Komma trennen. Bereiche von Artikelnummern gehen auch: <code>100-123</code></li>
            <li>Einzelne Artikelnummern oder Bestellungsnummern können durch folgende Schreibweise mehrfach ausgedruckt werden: <code>5x1337</code></li>
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

    # <editor-fold desc="explode input to array of product ids and purchase order ids
    // and make bitterkeitsinput to executable input">
    # simplify: separator: ',' and to lower. Watch out: ' - ' -> ',-,'
    $input_ids = strtolower(str_replace(array(",", ";", "|", " ", 'und', 'and'), ",", $_POST["etiketten"]));
    # simplify: '·' / 'mal' / 'times' -> 'x'
    $input_ids = str_replace(array('·', 'mal', 'times'), 'x', $input_ids);
    # <editor-fold desc="translate language ;)">
    $input_ids = str_replace(array('ein', 'eins', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben', 'acht', 'neun', 'zehn', 'elf', 'zwölf'),
        array('1', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'), $input_ids);
    $input_ids = str_replace(array('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'),
        array('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'), $input_ids);
    $input_ids = str_replace(array('trololol'),
        array('1337'), $input_ids);
    # </editor-fold>
    # simplify: ',,,,' -> ','
    while(strpos($input_ids, ',,')) { $input_ids = str_replace(",,", ",", $input_ids); }
    # simplify: ',123,-,125' -> '123-125'
    $input_ids = trim(str_replace(array(",-", "-,"), "-", $input_ids), ',');
    # simplify: '12 x 1337 -> 12x1337' (because ' ' is now ',', we have to replace ',' instead of ' '
    $input_ids = str_replace(',x', 'x', $input_ids);
    $input_ids = str_replace('x,', 'x', $input_ids);
    # creates an array containing the ids and id ranges
	$items=array_filter(explode(",",$input_ids));
	$items=expand_array_ranges($items);
    # </editor-fold>

	if (isset($_POST["type"])) {
        $action = $_POST["action"];

        $output = "";
        if ($_POST["type"] == "large") {
            die_friendly("zur Zeit deaktiviert");
            # $output=erzeuge_pdf($items, $print);
        } else if ($_POST["type"] == "small") {
            // kleine Etiketten für selbstklebendes Papier
            $output = generate_pdf_small($items, $action === 'print', $_POST["startposition"]);
        } else if ($_POST["type"] == "text") {
            $number=intval($_POST["number"]);
            if (($number < 1) || ($number > 25)) {
                die_friendly("Anzahl muss zwischen 1 und 25 liegen.");
            }
            for ($i=0;$i<$number;$i++) {
                print_text_label($_POST["etiketten"],$_POST["textlabel_type"]!=="multiple");
            }
        } else {
            die_friendly("What have you done?!?");
        }

        if ( $action === 'print' ) {
            # <editor-fold desc="print and display success message">
            insert_html_lines_top();

            echo '<p><b>Etiketten werden ausgedruckt.</b></p></br>
			<form action="index.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form>';

            insert_html_lines_bottom();
            # </editor-fold>
//        } elseif ( $action === 'select' ) {
//            # <editor-fold desc="display table to select the count of the labels">
//            insert_html_lines_top();
//
//            echo '
//            <form action="index.php" method="post" style="text-align: center">
//                <input type="hidden" name="etiketten" value="' . $_POST['etiketten'] . '">
//                <input type="hidden" name="type" value="' . $_POST['type'] . '">
//                <input type="hidden" name="startposition" value="' . $_POST['startposition'] . '">
//                <button type="submit" name="action" value="print" style="margin:2em">Drucken</button>
//                <table>
//                    <tbody>
//                        <tr class="head">
//                            <td>Nr.</td><td>Bezeichnung</td>
//                            <td>Preis</td>
//                            <td>Einheit</td>
//                            <td>Lieferant / Hersteller</td>
//                            <td>Anzahl</td>
//                        </tr>
//                        <tr class="newCateg">
//                            <td colspan="6">CNC / Drehbank</td>
//                        </tr>
//                        <tr>
//                            <td>0583</td>
//                            <td>Blöcke  (diverse, 10x100x100 bis 25x500x200 mm)</td>
//                            <td>5.00 €</td>
//                            <td>kg</td>
//                            <td>ebay batho2010 / B&amp;T: POM Restposten 5kg</td>
//                            <td><input type="number" value="1" max="20" min="0"></td>
//                        </tr>
//                        <tr>
//                            <td>0583</td>
//                            <td>Blöcke  (diverse, 10x100x100 bis 25x500x200 mm)</td>
//                            <td>5.00 €</td>
//                            <td>kg</td>
//                            <td>ebay batho2010 / B&amp;T: POM Restposten 5kg</td>
//                            <td><input type="number" name="count_0583" value="1" max="20" min="0"></td>
//                        </tr>
//                    </tbody>
//                </table>
//                <button type="submit" name="action" value="print" style="margin:2em" autofocus="">Drucken</button>
//            </form>
//            <form action="index.php"><input type="submit" value="Zur&uuml;ck"></form>
//            ';
//
//            insert_html_lines_bottom();
//            # </editor-fold>
        } else {
            # <editor-fold desc="display / download pdf">
            header('Content-type: application/pdf');
            header('Content-Disposition: attachment; filename="downloaded.pdf"');
            readfile($output);
            # </editor-fold>
        }
	} else {
        die_friendly("What have you done?!?");
	}
    # </editor-fold>
}
