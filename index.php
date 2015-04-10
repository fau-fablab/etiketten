<?php

/*
====================================================================


Etiketten-Templatesystem (C) Max Gaukler 2012
Public Domain / zur uneingeschränkten Verwendung freigegeben, keine Garantie für Funktionsfähigkeit

*/

/**
 * Inserts some HTML at the top of the document. This is needed for the FAU FabLab website style
 */
function insert_html_lines_top() {
    if ( defined('HTML_TOP') && HTML_TOP ) { return; }
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
    define('HTML_TOP', true);
}

/**
 * Inserts some HTML at the bottom of the document. This is needed for the FAU FabLab website style
 */
function insert_html_lines_bottom() {
    if ( defined('HTML_BOTTOM') && HTML_BOTTOM ) { return; }
	echo '</div>
	</div>

	<div id="bottom" class="bottom">
	</div>

    </body>
</html>';
    define('HTML_BOTTOM', true);
}

/**
 * Expands item ranges (123-125 -> 123,124,125)
 * @param $items array of items and item ranges
 * @return array of expanded items
 */
function expand_array_ranges( $items ) {
	$items_expanded = array();
	foreach ( $items as $i ) {
        $stroke_position = strpos( $i, "-" );
		if ( $stroke_position === FALSE ) {
            // normal entry, no range
            $items_expanded[] = $i;
        } elseif ( strpos( $i, 'po' ) !== FALSE ) {
            // purchase order
            $items_expanded = array_merge( $items_expanded, explode( '-', $i ) );
		} else {
			// number range
            # <editor-fold desc="get repeat statement">
            $pre = "";
            if( is_numeric( explode( 'x', substr( $i, 0, 3 ), 2 )[0] &&
                sizeof( explode( 'x', substr( $i, 0, 3 ), 2 ) ) === 2 ) ) {
                # the item starts with a repeat statement (btw: $i is already strtolower)
                $pre = intval(explode( 'x', substr( $i, 0, 3), 2)[0]) . 'x';
                $pos = strpos( $i, 'x' );
                $i = substr( $i, $pos + 1);
            }
            # </editor-fold>
            $stroke_position=strpos( $i,"-" );
			$start = intval(substr( $i,0,$stroke_position) );
			$end=intval(substr( $i,$stroke_position+1) );
			for ( $n = $start; $n <= $end; $n++ ) {
				$items_expanded[] = $pre . (string)$n;
			}
		}
	}
	return $items_expanded;
}

/**
 * @param $items array of product ids and purchase orders
 * @return string the html table
 */
function generate_preview_table( $items ) {
    $items_str="";
    foreach( $items as $item) {
        $items_str .= " " . $item;
    }

    if ( check_items_argument( $items_str ) ) {
        $std_out = execute_system_command( './svgtemplate.py --no-label ' . $items_str );
        $products = json_decode( $std_out );

        echo '
            <div id="preview" style="text-align: center">
                <table id="preview-table" style="margin: auto">
                    <thead>
                        <tr id="head" class="head">
                            <th>Nr.</th>
                            <th>Bezeichnung</th>
                            <th>Preis</th>
                            <th>Einheit</th>
                            <th>Ort</th>
                            <th>Anzahl</th>
                        </tr>
                    </thead>
                    <tbody>';

        foreach ( $products as $prod ) {
            echo '
                        <tr id="' . $prod->ID . '">
                            <td>' . $prod->ID . '</td>
                            <td>' . $prod->TITEL . '</td>
                            <td>' . $prod->PREIS . '</td>
                            <td>' . $prod->VERKAUFSEINHEIT . '</td>
                            <td>' . $prod->ORT . '</td>
                            <td><input type="number" name="#' . $prod->ID . '_count" value="' . $prod->COUNT . '" max="20" min="0"></td>
                        </tr>
                        <input type="hidden" name="#' . $prod->ID . '_titel" value="' . $prod->TITEL . '">
                        <input type="hidden" name="#' . $prod->ID . '_preis" value="' . $prod->PREIS . '">
                        <input type="hidden" name="#' . $prod->ID . '_verkaufseinheit" value="' . $prod->VERKAUFSEINHEIT . '">
                        <input type="hidden" name="#' . $prod->ID . '_ort" value="' . $prod->ORT . '">';
        }

        echo '
                    </tbody>
                </table>
            </div>';

    } else {
        die_friendly( "Ung&uuml;ltige Eingabe oder unerlaubtes Zeichen" );
    }
}

/**
 * generates labels in one pdf-file (uses svgtemplate.py) by product or purchase order ids
 * @param $items array of product ids and purchase orders
 * @param $print (True|False) if the generated pdf should be printed directly
 * @param $start_position int Always 0 for label printers that can print each label separately. For multiple labels on one page (e.g. with 16-label sheets on a normal printer), skip the first N places (because they were already used)
 * @return string the filename of the generated pdf (relative)
 */
function generate_pdf_small( $items, $print, $start_position ) {
	// Inkscape braucht ein schreibbares HOME
	putenv( "HOME=".getcwd()."/temp" );
    
	if (file_exists( './' . get_output_filename() ) ) {
		unlink( './' . get_output_filename() );
	}
	#chdir( "./SVG" );
	$items_str="";
	foreach( $items as $item ) {
		$items_str .= " " . $item;
	}

    if ( check_items_argument( $items_str ) ) {
        for ( $i = 0; $i < $start_position; $i++ ) {
            $items_str = "None " . $items_str;
        }

        print_r( execute_system_command( './svgtemplate.py ' . $items_str, '',
            'Das Erstellen der Etiketten war nicht erfolgreich.
            <br>Teste, ob die Schreib- und Leseberechtigungen stimmen
            <br>und ob eine Verbindung zum OpenERP aufgebaut werden konnte.' ) );

        #chdir( "../" );
        if ( $print ) {
            $btn = '<form action="' . get_output_filename() . '"><input type="submit" value="PDF ansehen"></form>';
            print_r( execute_system_command( 'lpr -P Zebra-EPL2-Label ./' . get_output_filename(), '',
                'Das Drucken der Etiketten war nicht erfolgreich.<br>' . $btn ) );
        }
        return './' . get_output_filename();
    } else {
        die_friendly( "Ung&uuml;ltige Eingabe oder unerlaubtes Zeichen" );
        return "";
    }
}

/**
 * generates labels in one pdf-file (uses svgtemplate.py) using json to provide the data for the labels
 * @param $post array of all HTTP post variables (=$_POST)
 * including at least 'start_position' and all '<id>_<title|preis|verkaufseinheit|ort>' variables
 * @return string the filename of the generated pdf (relative)
 */
function print_pdf_from_json( $post ) {
    // Inkscape braucht ein schreibbares HOME
    putenv( "HOME=".getcwd()."/temp" );

    if (file_exists( './' . get_output_filename() ) ) {
        unlink( './' . get_output_filename() );
    }

    # <editor-fold desc="generate json from post">
    $items = array();
    if ( $post['start_position'] > 0 ) {
        $empty_prod = new stdClass();
        $empty_prod->ID = '';
        $empty_prod->COUNT = $post['start_position'];
        $items[''] = $empty_prod;
    }
    foreach ( $post as $k => $count_val ) {
        if ( preg_match( '/^#\d{4}_count$/', $k ) === 1 ) {
            // if post variable is like "#<product_id>_count". Example: "#1337_count"
            $prod = new stdClass();
            $prod->ID = str_pad( intval( explode( '_', substr($k, 1), 2 )[0] ), 4, '0', STR_PAD_LEFT);
            if ( !isset( $items[$prod->ID] )
                && preg_match( '/^\d{1,2}$/', $count_val ) === 1
                && isset( $post['#' . $prod->ID . '_titel'] )
                && isset( $post['#' . $prod->ID . '_preis'] )
                && isset( $post['#' . $prod->ID . '_verkaufseinheit'] )
                && isset( $post['#' . $prod->ID . '_ort'] ) ) {

                $prod->COUNT = intval( $count_val );
                $prod->TITEL = $post['#' . $prod->ID . '_titel'];
                $prod->PREIS = $post['#' . $prod->ID . '_preis'];
                $prod->VERKAUFSEINHEIT = $post['#' . $prod->ID . '_verkaufseinheit'];
                $prod->ORT = $post['#' . $prod->ID . '_ort'];

                if ( $prod->COUNT > 0 ) {
                    if ( $prod->COUNT <= 20) {
                        $items[$prod->ID] = $prod;
                    } else {
                        die_friendly( "Anzahl muss zwischen 0 und 20 liegen." );
                    }
                }
            } else {
                var_dump($prod->ID);
                var_dump( !isset( $items[$prod->ID] ));
                var_dump(preg_match( '/^\d{1,2}$/', $count_val ) === 1);
                var_dump( isset( $post['#' . $prod->ID . '_titel'] ));
                var_dump( isset( $post['#' . $prod->ID . '_preis'] ));
                var_dump( isset( $post['#' . $prod->ID . '_verkaufseinheit'] ));
                var_dump( isset( $post['#' . $prod->ID . '_ort'] ) );
                die_friendly( "Ung&uuml;ltige oder unvollst&auml;ndige Eingabe" );
            }
        }
    }
    $items_json = json_encode( $items );

//    header('Content-Type: application/json');
//    print_r($items_str);
//    exit(0);
    # </editor-fold>

    if ( strlen( $items_json ) > 5 ) {
        # a valid json has more than 10 letters

        print_r( execute_system_command( './svgtemplate.py --json-input', $items_json,
            'Das Erstellen der Etiketten war nicht erfolgreich.
            <br>Teste, ob die Schreib- und Leseberechtigungen stimmen.' ) );

        $btn = '<form action="' . get_output_filename() . '"><input type="submit" value="PDF ansehen"></form>';
        print_r( execute_system_command( 'lpr -P Zebra-EPL2-Label ./' . get_output_filename(), '',
            'Das Drucken der Etiketten war nicht erfolgreich.<br>' . $btn ) );

        return './' . get_output_filename();
    } else {
        die_friendly( "Ung&uuml;ltige Eingabe oder unerlaubtes Zeichen" );
        return "";
    }
}

/**
 * Print plaintext labels
 * @param $text String: Text to print on the label
 * @param $oneLabel boolean True: make one big label with multiple lines
 *                          False: multiple labels, one per text line
 */
function print_text_label( $text,$oneLabel ) {
    $option="--multiple-labels";
    if ( $oneLabel ) {
        $option="--one-label";
    }
    print_r( execute_system_command( './textlabel.py --print ' . $option, $text ) );
}

/**
 * Executes a system command, using stdin, stdout, stderr
 * It dies friendly on errors
 * @param string $cmd : the command to be executed
 * @param string $stdin_text : the stdin text to be piped to the external program
 * @param string $error_message : a message that should be displayed, if an error occurres
 * @return string the stdout of the program
 */
function execute_system_command( $cmd, $stdin_text = '', $error_message = '' ) {
    // based on example code from http://php.net/manual/en/function.proc-open.php
    $descriptor_spec = array(
        0 => array( "pipe", "r" ), // stdin
        1 => array( "pipe", "w" ), // stdout
        2 => array( "pipe", "w" )  // stderr
    );

    $process = proc_open( $cmd, $descriptor_spec, $pipes);

    if (!is_resource( $process)) {
        die_friendly( "failed to run '" . $cmd . "'" );
    }

    // write to stdin
    fwrite( $pipes[0], $stdin_text );
    fclose( $pipes[0] );

    $stdout=stream_get_contents( $pipes[1] );
    fclose( $pipes[1] );

    $stderr=stream_get_contents( $pipes[2] );
    fclose( $pipes[2] );

    $return_value = proc_close( $process );
    if ( $return_value != 0 ) {
        if ( $error_message !== '' ) {
            die_friendly( $error_message );
        } else {
            die_friendly( "'" . $cmd . "' returned error $return_value:" . PHP_EOL . $stdout . PHP_EOL . $stderr );
        }
    }

    return $stdout;
}

/**
 * Checks if a string of items matches the regex rule and can be given to the python helpers
 * @param $items_str String: String on product and po-IDs
 * @return bool: Matches the regex rule
 */
function check_items_argument( $items_str ) {
    # preg_match( '/^[0-9]*$/',$items_str) === 1
    # preg_match( '/^( \d{1,4}| po\d{5}){1,50}$/', $items_str) === 1
    return preg_match( '/^( (\d{1,2}x)?(\d{1,4}|po\d{5})){1,50}$/', $items_str ) === 1;
    // regex explanation: matches ether a number up to 4 digits (-> for product ids)
    // or a string with 'po' and a 5 digits number (-> for purchase orders)
    // in front of it there might be a up to two digit number with an 'x' (12x1337 -> "12 times 1337" )
    // Such combinations are allowed up to 50 times and must begin at the start of the string and end at the end.
    // Problems: works only for lower case (strtolower is used when using $_POST['etiketten']) expressions
    // and only with leading ' ' (done in foreach above).
}

/**
 * Only displays the input form
 */
function show_input_form() {
    insert_html_lines_top();

    echo '<h2 id="erp"><label for="erp-label-input">ERP-Etiketten</label></h2>
        <form action="index.php" method="post" style="text-align: center"><label for="erp-label-input"><b>Artikelnummern (ERP: „interne Referenz“) oder Bestellungsnummern:</b></label>
            <input type="text" name="etiketten" id="erp-label-input" style="width:80%;margin:1em;text-align: center;font-size: large" placeholder="z.B.  541 123 9001 PO12345" autocomplete="off" autofocus> <br />
            <button type="submit" name="action" value="print">direkt Drucken</button>
            <button type="submit" name="action" value="select">Anzahl w&auml;hlen</button>
            <!--<button type="submit" name="action" value="preview">Vorschau anzeigen</button>-->
            <!-- BASTELEI: Format-Auswahl deaktiviert, hidden input der fest auf small und 0 bereits verbraucht stellt -->
            <input type="hidden" name="type" value="small"/>
            <input type="hidden" name="startposition" value="0"/>
		</form>
<hr/>
        <h2 id="free"><label for="free-text-area">Freitext-Eingabe</label></h2>
        <form action="index.php" method="post" style="text-align: center"><label for="free-text-area"><b>Text:</b></label> <br />
            <textarea name="etiketten" id="free-text-area" style="width:80%;margin:1em;text-align: center;font-size: large; height:5em;" placeholder="Hier Text eingeben - Auch mehrzeilig"></textarea><br />
            <label for="text-label-count">Anzahl:</label>
            <input type="number" name="number" id="text-label-count" value="1" min="1" max="25"/> St&uuml;ck<br/>
            <button type="submit" name="textlabel_type" value="multiple">Drucken: mehrere Etiketten<br/>eines pro Zeile</button>
            <button type="submit" name="textlabel_type" value="one">Drucken:<br />alles auf ein Etikett</button>
            <input type="hidden" name="type" value="text"/>
            <input type="hidden" name="action" value="print"/>
            <input type="hidden" name="startposition" value="0"/>
		</form>

        <hr/>

	    <p>Zum Drucken weiße Papier-Etiketten in den Etikettendrucker einlegen — nicht die silbernen!</p>
	    <p>Probleme bitte an die <a href="mailto:fablab-aktive@fablab.fau.de">Mailingliste</a> oder auf <a href="https://github.com/fau-fablab/etiketten">GitHub</a> melden.</p>


        <h3 style="margin-top:2cm" id="details">Details (ERP-Etiketten):</h3>
		<p>
	        <ul><li>Artikelnummern werden im ERP bei <code>interne Referenz</code> als vierstellige Zahl (mit f&uuml;hrenden Nullen) eingetragen, z.B. <code>0154</code>. Die f&uuml;hrenden Nullen k&ouml;nnen hier weggelassen werden.</li>
	        <li>Bestellungsnummern werdem im ERP unter <code>Einkauf / Angebote od. Bestellungen</code> in der &Uuml;berschrift angezeigt. Sie bestehen aus dem Pr&auml;fix <code>PO</code> und einer 5 stelligen Zahl (mit f&uuml;hrenden Nullen).</li>
	        <li>Mehrere Artikelnummern und Bestellungsnummern durch Leerzeichen oder Komma trennen. Bereiche von Artikelnummern gehen auch: <code>100-123</code></li>
            <li>Einzelne Artikelnummern oder Bestellungsnummern k&ouml;nnen durch folgende Schreibweise mehrfach ausgedruckt werden: <code>5x1337</code></li>
            <li>Der aufgedruckte Ort wird als Lagerort des Artikels oder der Kategorie eingetragen. (Kategorien vererben den Ort nicht an Unterkategorien!)</li>
	        <li>Die Artikelnummern k&ouml;nnen in <a href="https://eichhörnchen.fablab.fau.de">OpenERP</a> oder in der <a href="https://user.fablab.fau.de/~buildserver/pricelist/output/">Teile &Uuml;bersicht</a> nachgeschaut werden.</li>
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
}

/**
 * Displays an error message and then it dies
 * @param $message string error message to display
 */
function die_friendly( $message ) {
    insert_html_lines_top();
    echo '<div class="error"><p>Es trat ein Fehler auf:</p><p>' . $message . '</p></div></br>
			<form action="index.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form><br /><p>R.I.P.</p>';
    insert_html_lines_bottom();
    die();
}

/**
 * @param $str_input String: product and purchase order ids from input field
 * @return array containing one entry per id (this is also possible <number>x<id>)
 */
function process_ids_input( $str_input ) {
    if ( ! sizeof( $str_input ) ) {
        die_friendly( 'Die Eingabe war leer.' );
    }
    # <editor-fold desc="evaluate POST["etiketten"] input">
    //print_r( $_POST);

    # <editor-fold desc="make bitterkeitsinput to executable input and expand ranges">
    # simplify: separator: ',' and to lower. Watch out: ' - ' -> ',-,'
    $input_ids = strtolower( str_replace( array( ",", ";", "|", " ", 'und', 'and' ), ",", $str_input ) );
    # simplify: '·' / 'mal' / 'times' -> 'x'
    $input_ids = str_replace( array( '·', 'mal', 'times' ), 'x', $input_ids );
    # simplify: '–' / 'bis' / 'to' -> '-'
    $input_ids = str_replace( array( '–', 'bis', 'to' ), '-', $input_ids );
    # <editor-fold desc="translate language ;)">
    $input_ids = str_replace( array( 'ein', 'eins', 'einen', 'eine', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben', 'acht', 'neun', 'zehn', 'elf', 'zwölf' ),
        array( '1', '1', '1', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12' ), $input_ids );
    $input_ids = str_replace( array( 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve' ),
        array( '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12' ), $input_ids );
    $input_ids = str_replace( array( 'bitte', 'die', 'den', 'aber', 'flott', 'schnell' ), '', $input_ids ); # ;)
    $input_ids = str_replace( array( 'trololol', 'bestellung,nummer,', 'bestellnummer', 'bestellung' ),
        array( '1337', 'po', 'po', 'po', 'po', 'po' ), $input_ids);
    # </editor-fold>
    # simplify: ',,,,' -> ','
    while (strpos( $input_ids, ',,' )) {
        $input_ids = str_replace( ",,", ",", $input_ids);
    }
    # simplify: ',123,-,125' -> '123-125'
    $input_ids = trim( str_replace( array( ",-", "-," ), "-", $input_ids ), ',' );
    # simplify: '12 x 1337 -> 12x1337' (because ' ' is now ',', we have to replace ',' instead of ' ' )
    $input_ids = str_replace( ',x', 'x', $input_ids);
    $input_ids = str_replace( 'x,', 'x', $input_ids);
    # simplify: 'po ' -> 'po'
    $input_ids = str_replace( array( 'po,' ), array( 'po' ), $input_ids);
    # creates an array containing the ids and id ranges
    $items = array_filter(explode( ",", $input_ids) );
    return expand_array_ranges( $items );
    # </editor-fold>
//    # <editor-fold desc="TODO Idee: simplify input">
//    $product_ids_count = array();
//    foreach ( $items as $item ) {
//        # TODO: use n x id
//        if ( in_array( $item, $product_ids_count) && !strpos( $item, 'po' ) ) {
//            $product_ids_count[$item] += 1;
//        } else {
//            $product_ids_count[$item] = 1;
//        }
//    }
//    # TODO: use product_ids_count
//    # </editor-fold>
}

/**
 * Simply returns the filename that should be generated (inspecting the POST vars)
 */
function get_output_filename() {
    if( isset( $_POST['type'] ) && $_POST['type'] === 'text' ) {
        return 'temp/textlabel.pdf';
    } else {
        return 'temp/output-etikettenpapier.pdf';
    }
}


if( empty( $_POST["action"] ) ) {
    show_input_form();
    exit(0);
} else {
    # print_r( $_POST );

    $action = $_POST["action"];

    if ( isset( $_POST["etiketten"] )
        && !( isset( $_POST["type"] ) && $_POST["type"] === 'text' )
        && !( isset( $_POST["type"] ) && $_POST["type"] === 'print-selection' ) ) {
        $items = process_ids_input( $_POST["etiketten"] );
    }

    if ( $action === 'select' ) {
        # <editor-fold desc="display table to select the count of the labels">
        insert_html_lines_top();

        if ( sizeof( $items ) > 0 ) {
            echo '
                <form action="index.php" method="post" style="text-align: center">
                <input type="hidden" name="type" value="' . $_POST['type'] . '">
                <input type="hidden" name="startposition" value="' . $_POST['startposition'] . '">
                <button type="submit" name="action" value="print-selection" style="margin:2em">Drucken</button>';

            generate_preview_table( $items );

            echo '
                <button type="submit" name="action" value="print-selection" style="margin:2em" autofocus="">Drucken</button>
            </form>';
        } else {
            die_friendly( "Ung&uuml;ltige Eingabe oder unerlaubtes Zeichen" );
        }


        echo '<form action="index.php"><input type="submit" value="Zur&uuml;ck"></form>
        ';

        insert_html_lines_bottom();
        # </editor-fold>
    } elseif ( $action === 'print-selection' ) {
        # <editor-fold desc="print labels after the count of each label was selected in the table">

        if ( $_POST['type'] === 'small' ) {
            print_pdf_from_json( $_POST );
        } else {
            die_friendly( "What have you done?!?" );
        }

        insert_html_lines_top();

        echo '<p><b>Etiketten werden ausgedruckt.</b></p></br>';
        echo '<form action="' . get_output_filename() . '"><input type="submit" value="PDF ansehen"></form>';
        echo '<form action="index.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form>';

        insert_html_lines_bottom();
        # </editor-fold>
    } else {

        # <editor-fold desc="Generate labels">
        $output = "";
        if ( $_POST["type"] === "large" ) {
            die_friendly( "zur Zeit deaktiviert" );
            # $output=generate_pdf( $items, $print);
        } else if ( $_POST["type"] === "small" ) {

            // kleine Etiketten für selbstklebendes Papier
            $output = generate_pdf_small($items, $action === 'print', $_POST["startposition"]);
        } elseif ( $_POST["type"] === "text" ) {
            $number = intval( $_POST["number"] );
            if ( ( $number < 1 ) || ( $number > 25 ) ) {
                die_friendly( "Anzahl muss zwischen 1 und 25 liegen." );
            }
            for ( $i = 0; $i < $number; $i++ ) {
                print_text_label( $_POST["etiketten"], $_POST["textlabel_type"] !== "multiple" );
            }
        } else {
            die_friendly( "What have you done?!?" );
        }
        # </editor-fold>

        if ( $action === 'print' ) {
            # <editor-fold desc="print and display success message">
            insert_html_lines_top();

            echo '<p><b>Etiketten werden ausgedruckt.</b></p></br>';
            echo '<form action="' . get_output_filename() . '"><input type="submit" value="PDF ansehen"></form>';
            echo '<form action="index.php"><input type="submit" value="Zur&uuml;ck" autofocus=""></form>';

            insert_html_lines_bottom();
            # </editor-fold>
        } else {
            # <editor-fold desc="display / download pdf">
            header( 'Content-type: application/pdf' );
            header( 'Content-Disposition: attachment; filename="downloaded.pdf"' );
            readfile( $output );
            # </editor-fold>
        }

	}
// else {
//        die_friendly( "What have you done?!?" );
//	}
    # </editor-fold>
}
