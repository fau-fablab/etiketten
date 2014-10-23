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
	unlink("./temp/output-etikettenpapier.pdf");
	#chdir("./SVG");
	$items_str="";
	foreach($items as $item) {
		$items_str .= " " . $item;
	}
	if (preg_match('/^[0-9 ]*$/',$items_str)!==1) {
		die("illegal character in ID");
	}
	for ($i=0;$i<$startposition;$i++) {
		$items_str="None " . $items_str;
	}
	
	system("./svgtemplate.py ".$items_str);
	#chdir("../");
	if ($print) {
		system("lpr -P Zebra-EPL2-Label ./temp/output-etikettenpapier.pdf");
	}
	return "./temp/output-etikettenpapier.pdf";
}



if (empty($_POST["etiketten"])) {
	insert_html_lines_top();
	echo '<form action="elektro-etiketten.php" method="post"><b>IDs:</b> <input name="etiketten" type="text" size="40" class="form-text required"> <input type="submit" name="ok" value="weiter" class="form-submit">
	<br><span style="color:gray;"> Beispieleingabe: <tt>154 341 44 100-110</tt>
	</form>';
	insert_html_lines_bottom();
} else {
	$items=array_filter(explode(" ",$_POST["etiketten"]));
	$items=expand_array_ranges($items);
	if (isset($_POST["type"])) {
		$print=isset($_POST["print"]);
		
		$output="";
		if ($_POST["type"]=="gross") {
			$output=erzeuge_pdf($items,$print);
		} else {
			// kleine Etiketten für selbstklebendes Papier
			$output=erzeuge_pdf_klein($items,$print,$_POST["startposition"]);
		}
		
		if ($print) {
			insert_html_lines_top();
			echo '<p><b>Etiketten werden ausgedruckt.</b></p></br>
			<form action="elektro-etiketten.php"><input type="submit" value="Zur&uuml;ck" class="form-submit"></form>';
			insert_html_lines_bottom();
		} else {
			header('Content-type: application/pdf');
			header('Content-Disposition: attachment; filename="downloaded.pdf"');
			readfile($output);
		}
	} else {
		// IDs wurden eingegeben, jetzt die Frage nach der Seitengröße
		insert_html_lines_top();
		echo '<form action="elektro-etiketten.php" method="post">IDs: <input name="etiketten" type="text" value="'.htmlspecialchars($_POST["etiketten"]).'" class="form-text required"></br></br>
		<ul><li><b>Bitte angeben:</b> Format:
		<select name="type" size="1">
		  <option value="klein">klein (6x3cm), Selbstklebe-Etikettenpapier (f&uuml;r Schubladenmagazine)</option>
		  <!-- <option value="gross">groß (ca 8x10cm), normales Papier (f&uuml;r Elektronik-T&uuml;tchen)</option> -->
		</select></br></br>
		</li><li>
		<b>Bitte angeben:</b> Wie viele Etiketten auf diesem Bogen wurden bereits verbraucht?
		<input type="text" value="0" name="startposition" class="form-text required"></br></br>
		</li></ul>
		<input type="submit" name="pdf" value="PDF zeigen" class="form-submit"><input type="submit" name="print" value="Drucken (vorher ggf. Etikettenpapier einlegen!)" class="form-submit"> </form>
		<p>Zum Drucken Etikettenpapier in den manuellen Einzug des Druckers einlegen, bedruckbare Seite nach oben.</p>';
		insert_html_lines_bottom();
	}
 	
}


?>
