set nfacs [ gtkwave::getNumFacs ]
set all_facs [list]
for {set i 0} {$i < $nfacs } {incr i} {
    set facname [ gtkwave::getFacName $i ]
    lappend all_facs "$facname"
}

set num_added [ gtkwave::addSignalsFromList $all_facs ]
gtkwave::/Time/Zoom/Zoom_Full