<?php

/*
====================================================================


Etiketten-Templatesystem (C) Max Gaukler 2012
Public Domain / zur uneingeschränkten Verwendung freigegeben, keine Garantie für Funktionsfähigkeit

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

function insert_html_lines_bottom() {
	echo '</div>
	</div>


	<div id="bottom" class="bottom">
	</div>

    </body>
</html>';
}

function expand_array_ranges($items) {
	$items_expanded=array();
	// 123-125 umwandeln in 123,124,125
	foreach ($items as $i) {
		$strich_position=strpos($i,"-");
		if ($strich_position===FALSE) {
			// ganz normaler Eintrag, kein Nummernbereich
			$items_expanded[]=$i;
		} else {
			// Nummernbereich
			$von = intval(substr($i,0,$strich_position));
			$bis=intval(substr($i,$strich_position+1));
			for ($n=$von; $n <= $bis; $n++) {
				$items_expanded[]=(string) $n;
			}
		}
	}
	return $items_expanded;
}


function erzeuge_pdf_klein($items,$print,$startposition) {
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

	if (preg_match('/^[0-9]*$/',$items_str)===1) {
		// internal reference
		for ($i = 0; $i < $startposition; $i++) {
			$items_str = "None " . $items_str;
		}

		system("./svgtemplate.py " . $items_str);
		#chdir("../");
		if ($print) {
			system("lpr -P Zebra-EPL2-Label ./temp/output-etikettenpapier.pdf");
		}
		return "./temp/output-etikettenpapier.pdf";
	} elseif (preg_match('/.*PO[0-9][0-9][0-9][0-9][0-9]*$/',$items_str)===1) {
		// Bestellung
		for ($i = 0; $i < $startposition; $i++) {
			$items_str = "None " . $items_str;
		}
		#system("./svgtemplate.py " . $items_str);
		var_dump($items_str);
		#chdir("../");
		if ($print) {
			system("lpr -P Zebra-EPL2-Label ./temp/output-etikettenpapier.pdf");
		}
		return "./temp/output-etikettenpapier.pdf";
	} else {
		die("illegal character in ID");
	}
}



if (empty($_POST["etiketten"])) {
		// IDs wurden eingegeben, jetzt die Frage nach der Seitengröße
		insert_html_lines_top();
		echo '<form action="elektro-etiketten.php" method="post"><b>Artikelnummern (ERP: "interne Referenz"):</b> <input name="etiketten" type="text" size="40" placeholder="z.B.  541 123 9001" autocomplete="off">
		<input type="submit" name="print" value="Drucken">    <input type="submit" name="pdf" value="anzeigen" style="font-weight:normal; background:linear-gradient(to bottom, #B3C6D3 0%, #95A8B4 100%);"> 
		<!-- BASTELEI: Format-Auswahl deaktiviert, hidden input der fest auf klein und 0 bereits verbraucht stellt -->
		<input type="hidden" name="type" value="klein"/>
		<input type="hidden" name="startposition" value="0"/>
		</form>


		<p>Zum Drucken weiße Papier-Etiketten in den Etikettendrucker einlegen — nicht die silbernen!</p>
		<p>Probleme bitte an die <a href="mailto:fablab-aktive@fablab.fau.de">Mailingliste</a> oder auf <a href="https://github.com/fau-fablab/etiketten">GitHub</a> melden.</p>

		<p style="margin-top:2cm"> Details:
	<ul><li>Artikelnummern werden im ERP bei "interne Referenz" als vierstellige Zahl (mit führenden Nullen) eingetragen, z.B. <code>0154</code>. Die führenden Nullen können hier weggelassen werden.</li>
	<li>Mehrere Artikelnummern durch Leerzeichen oder Komma trennen. Bereiche von Artikelnummern gehen auch: <code>100-123</code></li>
	<li>Der aufgedruckte Ort wird als Lagerort des Artikels oder der Kategorie eingetragen. (Kategorien vererben den Ort nicht an Unterkategorien!)</li>
	<li>Die Artikelnummern können in <a href="https://eichhörnchen.fablab.fau.de">OpenERP</a> oder in der <a href="https://user.fablab.fau.de/~buildserver/pricelist/output/">Teile Übersicht</a> nachgeschaut werden.</li>
	</ul></p>



		<!-- <ul><li><b>Bitte angeben:</b> Format:
		<select name="type" size="1">
		  <option value="klein">klein (6x3cm), Selbstklebe-Etikettenpapier (f&uuml;r Schubladenmagazine)</option>
		  <option value="gross">groß (ca 8x10cm), normales Papier (f&uuml;r Elektronik-T&uuml;tchen)</option> 
		</select></br></br>
		</li>
		<li>
		<b>Bitte angeben:</b> Wie viele Etiketten auf diesem Bogen wurden bereits verbraucht?
		<input type="text" value="0" name="startposition"></br></br>
		</li></ul> -->


		';
		insert_html_lines_bottom();
} else {
	//print_r($_POST);
	$items=array_filter(explode(",",str_replace(array(",", ";", "|"), ",", $_POST["etiketten"])));
	$items=expand_array_ranges($items);
	if (isset($_POST["type"])) {
		$print=isset($_POST["print"]);

		$output="";
		if ($_POST["type"]=="gross") {
			die("zur zeit deaktiviert");
			# $output=erzeuge_pdf($items, $print);
		} else {
			// kleine Etiketten für selbstklebendes Papier
			$output=erzeuge_pdf_klein($items,$print,$_POST["startposition"]);
		}

		if ($print) {
			insert_html_lines_top();
			echo '<p><b>Etiketten werden ausgedruckt.</b></p></br>
			<form action="elektro-etiketten.php"><input type="submit" value="Zur&uuml;ck"></form>';
			insert_html_lines_bottom();
		} else {
			header('Content-type: application/pdf');
			header('Content-Disposition: attachment; filename="downloaded.pdf"');
			readfile($output);
		}
	} else {

	}
}
