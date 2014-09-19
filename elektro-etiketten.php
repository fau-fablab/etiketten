<?php

/*
====================================================================


Etiketten-Templatesystem (C) Max Gaukler 2012
Public Domain / zur uneingeschränkten Verwendung freigegeben, keine Garantie für Funktionsfähigkeit

*/

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
		system("lpr -P etiketten ./temp/output-etikettenpapier.pdf");
	}
	return "./temp/output-etikettenpapier.pdf";
}



if (empty($_POST["etiketten"])) {
	echo '<html><body><form action="elektro-etiketten.php" method="post">IDs: <input name="etiketten" type="text" size="40"> <input type="submit" name="ok" value="weiter"> </form></body></html>';
} else {
	$items=array_filter(explode(" ",$_POST["etiketten"]));
	$items=expand_array_ranges($items);
	if (isset($_POST["type"])) {
		$print=isset($_POST["print"]);
		
		if ($print) {
			echo '<html><body>Etiketten werden ausgedruckt. <form action="elektro-etiketten.php"><input type="submit" value="Zurück"></form></body></html>';
		}
		$output="";
		if ($_POST["type"]=="gross") {
			$output=erzeuge_pdf($items,$print);
		} else {
			// kleine Etiketten für selbstklebendes Papier
			$output=erzeuge_pdf_klein($items,$print,$_POST["startposition"]);
		}
		
		if (!$print) {
			header('Content-type: application/pdf');
			header('Content-Disposition: attachment; filename="downloaded.pdf"');
			readfile($output);
		}
	} else {
		// IDs wurden eingegeben, jetzt die Frage nach der Seitengröße
		header('Content-Type:text/html; charset=UTF-8');
		echo '<html><body><form action="elektro-etiketten.php" method="post">IDs: <input name="etiketten" type="text" value="'.htmlspecialchars($_POST["etiketten"]).'"><br>
		<b> Bitte angeben: </b><br>
		<b>Format: </b>
		<select name="type" size="1">
		<option value="klein">klein (6x3cm), Selbstklebe-Etikettenpapier (für Schubladenmagazine)</option>
		<!-- <option value="gross">groß (ca 8x10cm), normales Papier (für Elektronik-Tütchen)</option> -->
		</select><br><b>bitte angeben:</b> Wie viele Etiketten auf diesem Bogen wurden bereits verbraucht? <input type="text" value="0" name="startposition"><br><input type="submit" name="pdf" value="PDF zeigen"><input type="submit" name="print" value="Drucken (vorher ggf. Etikettenpapier einlegen!)"> </form><br>Zum Drucken Etikettenpapier in den manuellen Einzug des Druckers einlegen, bedruckbare Seite nach oben.</body></html>';
	}
 	
}


?>
