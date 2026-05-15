#!/usr/bin/perl 

# alpaco.pl
# Program to take paralell texts in 2 languages and allow a user
# to manually align the words/phrases.
#
# Copyright (C) 2002
# Ted Pedersen, University of Minnesota, Duluth
# tpederse@d.umn.edu
# Brian Rassier, University of Minnesota, Duluth
# rass0028@d.umn.edu
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#-----------------------------------------------------------------------------
#                              Start of program
#-----------------------------------------------------------------------------

#define colors for possible and phrasal edges
$possible_color="light green";
$phrasal_color="red";

#allows the use of Tk
use Tk;

#this loads the HistEntry module if possible, otherwise just uses regular entry widgets
$Entry = "Entry";
eval {
    #try loading the module, otherwise $Entry is left to the value "Entry"
    require Tk::HistEntry;
    $Entry = "HistEntry";
};


#Loads the SimpleFileSelect module if possible, otherwise defaults to a label
$SimpleFileSelect = "Label";
eval{
    require Tk::SimpleFileSelect;
    $SimpleFileSelect = "SimpleFileSelect";
};


#needed for the floor function, used to interpret Blinker files
use POSIX qw(ceil floor);

#-----------------------------------------------------------------------------
#MAKE THE INTERFACE/WIDGETS 
#-----------------------------------------------------------------------------

#These are the colors for the word buttons.  They can be changed here, then they are
#changed throughout the code.  
$normal = "light gray";
$connected = "light blue";
$nullback = "black";
$nullfore = "orange";



#for indexes in my checkbutton widget arrays
$size1 = $size2 = $active1 = $active2 = 0;

#set these variables to Blinker as Default
$v = 10; #verses per file
$sam = 25; #samples of files
$an = 7; #annotators


#set flag for resizing to -1
$bopenflag = -1;

#set $blinkfile to "" so we can tell if there has been a blinker file opened
$blinkfile = "";

my $mw = MainWindow->new(-height,750,-width,660);
$mw->packPropagate(0);
$mw->title("Aligner for Parallel Corpora (Alpaco)");
#$mw->geometry("550x550");

#frame for entry and labels
$frametop = $mw->Frame->pack(-side,'top',-fill,'x');

#frame for canvas widget
$frameleft = $mw->Frame->pack(-side,'left',-fill,'y');

#frame for main buttons
$frameright = $frameleft->Frame->pack(-side,'right',-fill,'y');

#frame for menus
$frametoptop = $frametop->Frame->pack(-side,'top',-fill,'x');
$frametopbottom = $frametoptop->Frame->pack(-side,'bottom',-fill,'x');
#informational label button
$frametoptop->Label(-textvariable,\$info,-relief,'ridge',-width,70)->pack(-side,'right',
									  -fill,'x');
#label for entry1
#$frametop->Label(-text,"Source File:")->pack(-side,'left',-anchor,'w');

#entry widget 1
#$entry1_w = $frametop->$Entry(-textvariable,\$file1,
#				 -background,"white",
#				 -takefocus,1)->pack(-side,'left',
#						     -anchor,'w');

#starts the cursor at the entry1 widget
#$entry1_w->focus();

#label for entry2
#$frametop->Label(-text,"Target File:")->pack(-side,'left',-anchor,'w');

#entry widget 2
#$entry2_w = $frametop->$Entry(-textvariable,\$file2,
#			     -background,"white")->pack(-side,'left',
#							-anchor,'w');

#checkbutton for line by line
# $cb = $frametop->Checkbutton(-text,'Line-By-Line',-variable,\$cb_value,-relief,'ridge',
#			     -command,\&lbyl)->pack(-side,'left');

#button for line-by-line, don't pack it until line-by-line is on
$nl = $frametopbottom->Button(-text,'Next Line',-command,\&load_files)->pack(-side,'right');
$pl = $frametopbottom->Button(-text,'Prev Line',
			-command,sub{
			    #decrement the line number, then load the files
			    $linenum = $linenum - 2;
			    $linenum2 = $linenum2 - 2;
			    &load_files})->pack(-side,'right');
##########MENUS##########
#makes the file menu
$frametoptop->Menubutton(-text,"File",			   
			 -menuitems,[
				     #This option is pretty silly. It just simulates pressing the enter key for each entry field.  I commented it out to try alpaco without it.
				     #['command',"Open Text Files",-command,\&load_files],
#				     ['command',"Find Text Files",-command,\&find],
#				     "-",
#				     ['command',"Save Current Work to File",-command,\&save_blink],
#				     "-",
#				     ['command',"Open an Alpaco File",-command,\&open_pop],
				     ['command',"Save an Alpaco File",-command,\&save2],
				     "-",
#				     ['command',"Clear Connections",-command,\&clear_lines],
#				     ['command',"Clear All",-command,\&clear_tot],				     
#				     "-",
				     ['command',"Exit",-command,sub{
					 #removes the temporary files that were made if present
					 system("rm Blinktemp1 Blinktemp2") if(open(FP1,"Blinktemp1"));
					 system("rm sizetemp SizeVerse1 SizeVerse2") if(open(FP1,"sizetemp"));
					 exit;}]],			
			 -tearoff,0)->pack(-side,'left',
					   -anchor,'w');

#makes the options menu
$frametoptop->Menubutton(-text,"Options",
			 -menuitems,[['command',"Connect",-command,\&con],
#				     ['command',"Null Connect",-command,\&nullcon],
				     ['command',"Disonnect",-command,\&undo],
#				     ['command',"Redraw Connect",-command,\&redo],  
				     "-",
#				     ['command',"View Sentences",-command,\&show_sentences], 
#				     ['command',"Change Mode",-command,\&chmode], 
#				     ['command',"Change Data Limits",-command,\&data_pop]
                                    ],
			 -tearoff,0)->pack(-side,'left',
					   -anchor,'w');

#makes the help menu widget
$frametoptop->Menubutton(-text,"Help",
			 -menuitems,[
#                                    ['command',"Help",-command,\&help_pop],
#				     ['command',"Keyboard Shortcuts",-command,\&kbd_pop],
				     ['command',"About",-command,\&about_pop]],
			 -tearoff,0)->pack(-side,'left',
					   -anchor,'w');

##########MENUS END##########

##########MAIN BUTTONS##########
#connect button
$frametopbottom->Button(-text,"Sure", -command,\&con,
			-background,$connected,
			-activebackground,'blue'
			)->pack(-side,'left',-anchor,'w',-fill,'x');
#possible connect button
$frametopbottom->Button(-text,"Possible", -command,\&possible,
			-background,$possible_color,
			-activebackground,'blue'
			)->pack(-side,'left',-anchor,'w',-fill,'x');
#possible connect button
$frametopbottom->Button(-text,"Phrasal", -command,\&phrasal,
			-background,$phrasal_color,
			-activebackground,'blue'
			)->pack(-side,'left',-anchor,'w',-fill,'x');
#null connect button
#$frametopbottom->Button(-text,"Null Connect", -command,\&nullcon,
#			-activebackground,"blue",
#			-background,$nullback,
#			-foreground,$nullfore)->pack(-side,'left',-anchor,'w',-fill,'x');
#undo button 
$frametopbottom->Button(-text,"Disconnect", -command,\&undo,
			-activebackground,"blue"
			)->pack(-side,'left',-anchor,'w',-fill,'x');
#redo button
#$frametopbottom->Button(-text,"Redraw (one line)", -command,\&redo,
#			-activebackground,"blue"
#			)->pack(-side,'left',-anchor,'w',-fill,'x');
##########MAIN BUTTONS END##########


##########NEXT/PREV BLINKER OPTION##########
#makes a frame for the next/previous buttons
$nextframe = $frameright->Frame->pack(-fill,'x');

#prev button
$prev = $nextframe->Button(-text,"<Prev", -command,sub{$prev->focus;&next},
			   -activebackground,"blue",
			   #-background,"dark green",
			   #-foreground,"white"
			   );


#next button
$next = $nextframe->Button(-text,"Next>", -command,sub{$next->focus;&next},
			   -activebackground,"blue",
			   #-background,"dark green",
			   #-foreground,"white"
			   );
##########NEXT/PREV BLINKER OPTION END##########


##########NEXT/PREV BLINKER ANNOTATOR OPTION##########
#makes a frame for the next/previous buttons for annotator
$nextanframe = $frameright->Frame->pack(-fill,'x');

#prev button
$prevan = $nextanframe->Button(-text," <-- ", -command,sub{$prevan->focus;&nextan},
			       -activebackground,"blue",
			       #-background,"dark green",
			       #-foreground,"white"
			       );
#next button
$nextan = $nextanframe->Button(-text," --> ", -command,sub{$nextan->focus;&nextan},
			       -activebackground,"blue",
			       #-background,"dark green",
			       #-foreground,"white"
			       );
##########NEXT/PREV BLINKER ANNOTATOR OPTION END##########


##########BROWSE/EDITR OPTION##########
#makes a frame for the radio buttons
$radioframe = $frameright->Frame->pack(-fill,'x');

#makes the browse/edit checkbuttons and stores their IDs
#push @rb,$radioframe->Radiobutton(-text,'Browse',-value,'Browse',-variable,\$rb_value,
#				  -background,'black',-foreground,'white',
#				  -command,\&browse,-indicatoron,0);
#push @rb,$radioframe->Radiobutton(-text,'Edit',-value,'Edit',-variable,\$rb_value,
#				  -background,'black',-foreground,'white',
#				  -command,\&browse,-indicatoron,0);
#draws the widgets
#$rb[0]->pack(-side,'left',-padx,5,-pady,5);
#$radioframe->Label(-text,"  Mode  ",-relief,'ridge')->pack(-side,'left',-anchor,'w');
#$rb[1]->pack(-side,'left',-padx,5,-pady,5);

#invokes the browse button as a default
#$rb[0]->invoke;
##########BROWSE/EDITR OPTION END##########

#exit button
$frameright->Button(-text,"Save", -command, \&save2,
		    -activebackground,"blue"
		    )->pack(-side,'top',-anchor,'n',-fill,'x',-ipady,20, -ipadx, 60, -expand, 1);
$frameright->Label(-text => "k - down for English\ni - up for English\nl - down for Czech\no - up for Czech\n\nv - SURE connection\nc - POSSIBLE connection\nx - PHRASAL connection\n\nd - delete connection\n\nPageDown - next sentence\nPageUp - previous sentence\n\ns - save file\nq - save file and exit\n\n\n\n\n")->pack(-anchor, 'n', -side, 'top');

$frameright->Label(-text => "  Sentence number:")->pack(-anchor, 's', -side, 'left');
$frameright->Label(-textvariable => \$linenum)->pack(-side,'left');#->pack(-anchor, 's');
$frameright->Label(-text => "/")->pack(-side,'left');#->pack(-anchor, 's');
$frameright->Label(-textvariable => \$number_of_sentences)->pack(-side,'left');#->pack(-anchor, 's');
#View Sentences button
#$frameright->Button(-text,"View Sentences", -command,\&show_sentences,
#		    -activebackground,"blue"
#		    )->pack(-side,'top',-anchor,'w',-fill,'x',pady,10);

#makes the canvas widget, with a parent for binding reasons
$parentcanvas = $frameleft->Scrolled("Canvas",-background,
				     'white',-takefocus,1,-width,500)->pack(-side,'bottom',
									    -fill,'both',-expand,1);
$canvas = $parentcanvas->Subwidget("canvas");


#adds a buffer in the top of the canvas
$canvas->createText(30,30,-text," ");

##########binding keyboard shortcuts############
#define enter callback for entry one
#$entry1_w->bind("<Return>",\&load_1);

#define enter callback for entry one
#$entry2_w->bind("<Return>",\&load_2);

#Control + s saves
#n$mw->bind("<Control-Key-s>", \&save_pop);

#control + o opens
#$mw->bind("<Control-Key-o>", \&open_pop);

#Contryl + c quits
#$mw->bind("<Control-Key-c>", \&con);

#binds Ctrl + n to null connect 
#$mw->bind("<Control-Key-n>",\&nullcon);
#$mw->bind("<Key-d>",\&undo);

#binds Ctrl + c to connect when in list widgets
#$mw->bind("<Button-3>",\&con);
#$mw->bind("<Button-2>",\&undo);

#$mw->bind("<space>",\&con);
#$mw->bind("<Escape>",\&nullcon);
#$mw->bind("<Delete>",\&undo);

#$mw->bind("<Key-n>",\&autopair);
#$mw->bind("<Key-e>",\&autopairen);
#$mw->bind("<Key-q>",\&autopairposs);


#$mw->bind("<Key-m>",\&autoenprep);
#$mw->bind("<Key-M>",\&autoenprep2);
#$mw->bind("<Key-X>",\&autocrosspair);
#$mw->bind("<quotedbl>",\&autoczdouble);
#$mw->bind("<Key-j>",\&auto_enprepadjnoun_czadjnoun);
#$mw->bind("<Key-J>",\&auto_enprepadjadjnoun_czadjadjnoun);
#$mw->bind("<Key-t>",\&auto_enthat_czcommaze);

#create possible edge
#$mw->bind("<Key-p>",\&possible);
#$mw->bind("<Key-s>",\&possible);

#create phrasal edge
#$mw->bind("<Key-f>",\&phrasal);
#$mw->bind("<Key-a>",\&phrasal);

#my shortcuts
$mw->bind("<Key-k>",\&down1);
$mw->bind("<Key-l>",\&down2);
$mw->bind("<Key-i>",\&up1);
$mw->bind("<Key-o>",\&up2);
$mw->bind("<Key-v>",\&con);
$mw->bind("<Key-c>",\&possible);
$mw->bind("<Key-x>",\&phrasal);
$mw->bind("<Key-d>",\&undo);
$mw->bind("<Key-s>",\&save2);
$mw->bind("<Key-q>",\&save_and_exit);

# Prev and next lines
$mw->bind("<Next>",\&load_files);
$mw->bind("<Prior>",sub{
			    #decrement the line number, then load the files
			    $linenum = $linenum - 2;
			    $linenum2 = $linenum2 - 2;
			    &load_files});


#$mw->bind("<Control-Key-r>",\&redo);

##########binding keyboard shortcuts end############

#sets the buffer between widgets (words) in the canvas
$buff = 30;

#Start the main loop
$cb_value=1;

$file = $ARGV[0];
check_parametres();
$mw->title("Aligner for Parallel Corpora (Alpaco): $file");
if ($ARGV[1]=~/[0-9]*/) {
    print "Go to line number $ARGV[1]\n";
    $linenum=$ARGV[1]-1;
    $linenum2=$ARGV[1]-1;
#    load_files;
}  
load_1();
load_2();
load_output();
draw_lines();
MainLoop;

#-----------------------------------------------------------------------------
#Sub-routines
#-----------------------------------------------------------------------------


#function that loads both files if the menu item is pressed.  
#This function uses a sequence of flags from return values of the load_1 and load_2
#functions, in order to reuse code.
sub load_files{
    #set variables to 0
    $flag = $t1 = 0;

    #load source file, get return value
    $t1 =  &load_1;

    #set the flag if source file had errors
    $flag = 1 if $t1 < 0;
    $t1 = 0;
    $t1 = &load_2;

    #set the flag if target file had errors
    $flag += 2 if $t1 < 0;

    #check the results and let the user know if there were errors
    $info = "Editing $sentence_name[1][$linenum] and $sentence_name[2][$linenum2]";
    
    #set the scroll region now that items have been inserted
    $canvas->configure(-scrollregion,[ $canvas->bbox("all") ]);
    draw_lines();
}


sub init_selection {
  $canvas->yviewMoveto(0); 
  $active_token1 = 0;
  $id1[0]->select;
  $status1[0] = 1;
  $active_token2 = 0;
  $id2[0]->select;
  $status2[0] = 1;
  save2();
}

sub save_and_exit {
  save2();
  exit;
}

#-----------------------------------------------------------------------------
#load_files end

#two functions to load files into memory
sub load_file1_into_memory {
  if(!open(FILE, "<:encoding(utf-8)", "$file")){
    $info = "Error opening '$file'";
#    $entry1_w->bell();
    return(-1);
  }
#Loading of whole file into memory - sentences will be stored in two-dimensinal arry @whole_file1
  my $sentence_number=0;
  while (<FILE>) {
  
#beginnig of new sentence
    if ($_=~/<s id=\"(.*)\">/) {
#      print "$_";
      $sentence_number++;
      $sentence_name[1][$sentence_number]=$1;
    }
#put sentence into memory    
    if ($_=~/<english>(.*)<\/english>/) {
      @{$whole_file1[$sentence_number]} = split(/ /, $1);
    }
  }
  close (FILE);
  $number_of_sentences=$sentence_number;
}

sub load_file2_into_memory {
  if(!open(FILE, "<:encoding(utf-8)", "$file")){
    $info = "Error opening '$file'";
#    $entry1_w->bell();
    return(-1);
  }
#Loading of whole file into memory - sentences will be stored in two-dimensinal arry @whole_file1
  my $sentence_number=0;
  while (<FILE>) {
  
#beginnig of new sentence
    if ($_=~/<s id=\"(.*)\">/) {
#      print "$_";
      $sentence_number++;
      $sentence_name[2][$sentence_number]=$1;
    }
#put sentence into memory    
    if ($_=~/<czech>(.*)<\/czech>/) {
      @{$whole_file2[$sentence_number]} = split(/ /, $1);
    }
  }
  close (FILE);
}

#---------------------------------------------------------------------------

#function that loads the source file into the tool
sub load_1{
    if (!$loaded1) {
      $info = "opening file '$file1'...";
      print "Opening file $file1..... \n";
      load_file1_into_memory();
      $loaded1=1;
    }
    
    #clear out the old sentence
    undef $sentence1;

    #clears the previous connections
    &clear_lines;

    #remove the old words from the canvas
    while(@del1){
	$canvas->delete(pop @del1);
    }

    #clear the id's from the past file
    undef @del1;

    #clears the canvas text for file 1
    while(@id1){
	$d = (pop @id1);
	$d->destroy();
    }
    
    #undefines the id's for file 1
    undef @id1;

    #reset the status array for list 1
    $size1 = $active1 = 0;
    undef @status1;


	#increment the line number
	$linenum++;

#This if statement takes care of the line-by-line loading if necessary
	$linenum = 1 if($linenum < 1);

	#load the next line

	my @temp= @{$whole_file1[$linenum]};
	#check if there were any lines left, let the user know
	if(!$temp[0]){
	    $info = "No more lines in the file";
	    return;
	}

	#set the yvaraiable to the proper screen distance
	my $yvar = 50;
	
	#keep the sentence for viewing later
	$sentence1 = join(' ', @temp);
	

	#process the line word-by-word
#	print "Printing words : ";
	foreach my $word (@temp){
	    #make word labels
#	    print "$word "; 
	    $word = " " x (10-length($word)) . $word;
	    my $label1 = $canvas->Checkbutton(-text,$word,-relief,'ridge',-justify,'right',-takefocus,1,
					      -selectcolor,'yellow',-indicatoron,0,-variable,\$status1[$size1++],
					      -disabledforeground,'yellow',-activeforeground,'black');
	    
	    #keep track of $id for configuring the checkbuttons
	    push @id1,$label1;

	    #keep track of the actual object to delete it later
	    push @del1,$canvas->createWindow(150,$yvar,-anchor,'e',-window,$label1);

	    #increment the $yvar for the next object to insert
	    $yvar += $buff;    
	}    
	#change the scroll region because more objects were added
	$canvas->configure(-scrollregion,[ $canvas->bbox("all") ]);

#	close(FILE);

	#update informational label for user knowledge
	$info = "Line $linenum from file '$file' loaded";

	#make sure the words are enabled/disabled as needed
	&browse;

	#do not continue loading, because line-by-line is finished
#	print "\n";	
	return;
}
#-----------------------------------------------------------------------------
#load_1 end


#function that loads target file into the tool
sub load_2{
    #enables the flag for the size option
    $bopenflag = 0;
    
    if (!$loaded2) {
      $info = "opening file '$file2'...";
      print "Opening file $file2..... \n";
      load_file2_into_memory(); 
      $loaded2=1;
    }
    
#	print "Printing words of file2: ";
    
    #clear out the old sentence
    undef $sentence2;

    #clears the previous connections
    &clear_lines;

    #remove the old words from the canvas 
    while(@del2){
	$canvas->delete(pop @del2);
    }

    #clear the id's from the past file
    undef @del2;

    #clears the canvas text for file 2
    while(@id2){
	$d = (pop @id2);
	$d->destroy();
    }

    #undefines the id's from file 2
    undef @id2;
    
    
    #clear the status array for the checkbuttons in list 2
    $size2 = $active2 = 0;
    undef @status2;

	#increment the line number
	$linenum2++;

	#reset the line number if a new file was opened
	$linenum2 = 1 if($linenum2 < 1);


##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!change loading of sentence!!!!!!!!!!!!!!!!!!!!!!!!!!!++
	my @temp= @{$whole_file2[$linenum2]};
	#check if there were any lines left, let the user know
	if(!$temp[0]){
	    $info = "No more lines in the file";
	    return;
	}

	#set the yvaraiable to the proper screen distance
	my $yvar = 50;
	
	#keep the sentence for viewing later
	$sentence2 = join(' ', @temp);


	#process the line word-by-word
	foreach $word (@temp){
	    #make word labels
	    my $word = $word . " " x (10-length($word));
	    my $label2 = $canvas->Checkbutton(-text,$word,-relief,'ridge',-justify,'left',-takefocus,1,
					      -selectcolor,'yellow',-indicatoron,0,-variable,\$status2[$size2++],
					      -disabledforeground,'yellow',-activeforeground,'black');
	    
	    #keep track of $id for configuring the checkbuttons
	    push @id2,$label2;

	    #keep track of the actual object to delete it later
	    push @del2,$canvas->createWindow(300,$yvar,-anchor,'w',-window,$label2);

	    #increment the $yvar for the next object to insert
	    $yvar += $buff;    
	}
	#change the scroll region because more objects were added
	$canvas->configure(-scrollregion,[ $canvas->bbox("all") ]);


	#update informational label for user knowledge
	$info = "Line $linenum2 from file '$file2' loaded";

	#make sure the words are enabled/disabled as needed
	&browse;

	#exit the function because it is finished loading
	return;
}
#-----------------------------------------------------------------------------
#load_2 end


#loads file with connections done before, if it doesn't exist file is created
sub load_output {
  my $filename = shift;
  if(!open(OUTPUT_FILE, "<:encoding(utf-8)", "$file")){
    $info = "Error opening '$file', file will be created";
#    $entry1_w->bell();
    return;
  }
  my $sentence_number=0;
#  print "Loading sentences: ";  
  while (<OUTPUT_FILE>) {
  
#beginnig of new sentence
    if ($_=~/<s id=\"(.*)\">/) {
      $sentence_number++;
      next;
    }
    elsif ($_ =~ /<sure>(.*)<\/sure>/) {
      my @aligns = split(/ /, $1);
      foreach my $a (@aligns) {
        if ($a =~ /^(\d*)-(\d*)$/) {
          push @{$blinkarray[$sentence_number]}, "$1 $2";
        }
      }
    }
    elsif ($_ =~ /<possible>(.*)<\/possible>/) {
      my @aligns = split(/ /, $1);
      foreach my $a (@aligns) {
        if ($a =~ /^(\d*)-(\d*)$/) {
          push @{$possiblearray[$sentence_number]}, "$1 $2";
        }
      }
    }
    elsif ($_ =~ /<phrasal>(.*)<\/phrasal>/) {
      my @aligns = split(/ /, $1);
      foreach my $a (@aligns) {
        if ($a =~ /^(\d*)-(\d*)$/) {
          push @{$phrasalarray[$sentence_number]}, "$1 $2";
        }
      }
    }
  }
  close (OUTPUT_FILE);
}
#-------------------------------------------------------------------------------
#load_output end

sub check_parametres {
#  print "Checking parametres... \n";
  if (!(-e $file)) {
    print "Source file $file doesn't exist! \n";
    print "Usage: alpaco.pl <file> \n";
    exit;
  }
}  
  


#This function makes a "null connection" if a word in one file has no
#translation into the other file.
sub nullcon {   
    #clear out temp arrays @list1 and @list2 from past connections
    undef @list1;
    undef @list2;
    my $disconect_first;

    #These 2 while loops get the selected elements to connect
    my $i = 0;
    while($i < @status1){
	if($status1[$i]){
	    push @list1,$i;
	}
	$i++;
    }    
    $i = 0;
    while($i < @status2){
	if($status2[$i]){
	    push @list2,$i;
	}
	$i++;
    }
    

    #error checking if nothing was selected
    if(!@list1 && !@list2){
    	$info = "ERROR: Nothing Selected For Null connect";
	return;
    }

    #error checking if items from both lists were selected
    # if(@list1 && @list2){
    	# $info = "ERROR: Items Selected From Both Lists";
	# return;
    # }
    

    #This if statement is entered if there is something selected from the first
    #text file to "null connect", and there is nothing selected from file 2
    if(@list1){
		
	#this for loop makes a null connection for each selected item in the first list
	foreach (@list1) {
	    #save the indexes + 1 for the blinker-style file
	    $i = $_+1;

	    #looks through all the connections, and doesn't connect if the connection is 
	    #already there
	    $foundflag = 0;
	    foreach(@{$possiblearray[$linenum]}){
		if($_ =~ /^$i /){
		    $foundflag = 1;
		    $id1[$_]->deselect;
		    $info = "\"$whole_file1[$linenum][$i-1]\" needs to be disconnected first";
		    last;
		}
	    }	        
	    foreach(@{$blinkarray[$linenum]}){
		if($_ =~ /^$i 0$/){
		    $foundflag = 1;
		    $id1[$_]->deselect;
		    $info = "null connect to \"$whole_file1[$linenum][$_-1]\" has already been done";
		    last;
		}
		elsif ($_=~ /^$i /){
		    $foundflag = 1;
		    $info = "\"$whole_file1[$linenum][$i-1]\" needs to be disconnected first";
		    last;
		}
	    }
	    #skip this connection if it has already been done
	    next if($foundflag == 1);

	    #continue if connection hasn't been done yet
	    push @{$blinkarray[$linenum]}, "$i 0";
	    
	    #un-highlight the selected items,change to "null" color
	    $id1[$_]->deselect();
	    $id1[$_]->configure(-background, $nullback, -foreground, $nullfore,-disabledforeground,"white");
	    

	    #keep last element for easier use of the arrow keys
	    $active1 = $_;	    
	}
    }
    
    #This if statement is entered if there is something selected from the second
    #text file to "null connect", and there is nothing selected from file 1
    if(@list2){

	#this for loop makes a null connection for each selected item in the second list
	foreach (@list2) {
	    #save the indexes + 1 for the blinker-style file
	    $i = $_+1;
	    
	    #looks through all the connections, and doesn't connect if the connection is 
	    #already there
	    $foundflag = 0;
	    foreach(@{$possiblearray[$linenum]}){
		if($_ =~ / $i$/){
		    $foundflag = 1;
		    $id2[$_]->deselect;
		    $info = "\"$whole_file2[$linenum][$i-1]\" needs to be disconnected first";
		    last;
		}
	    }	        
	    foreach(@{$blinkarray[$linenum]}){
		if($_ =~ /^0 $i$/){
		    $foundflag = 1;
		    $id2[$_]->deselect;
		    $info = "null connect to \"$whole_file2[$linenum][$_-1]\"$_ has already been done";
		    last;
		} 
		elsif ($_=~ / $i$/){
		    $foundflag = 1;
		    $info = "\"$whole_file2[$linenum][$i-1]\" needs to be disconnected first";
		    last;
		}
	    }
	    #skip this connection if it has already been done
	    next if($foundflag == 1);

	    #continue if connection hasn't been done yet
	    push @{$blinkarray[$linenum]}, "0 $i";

	    #un-highlight the selected items
	    $id2[$_]->deselect();
	    $id2[$_]->configure(-background, $nullback, -foreground, $nullfore,-disabledforeground,"white");

	    #keep last element for easier use of the arrow keys
	    $active2 = $_;
	}
    }
}
#-----------------------------------------------------------------------------
#nullcon end


sub down1 {
  for (my $i = 0; $i < @id1; $i++) {
    if ($status1[$i]) {
      $id1[$i]->deselect;
      $active_token1 = $i;
    }
  }
  $active_token1++ if $active_token1 < $#id1;
  $id1[$active_token1]->select;
  $canvas->yviewScroll(2 => unit) if (70 + $buff * $active_token1 > $canvas->yview->[1] * ($canvas->bbox("all")->[3] - $canvas->bbox("all")->[1]));
}
  
sub down2 {
  for (my $i = 0; $i < @id2; $i++) {
    if ($status2[$i]) {
      $id2[$i]->deselect;
      $active_token2 = $i;
    }
  }
  $active_token2++ if $active_token2 < $#id2;
  $id2[$active_token2]->select;
  $canvas->yviewScroll(2 => unit) if (70 + $buff * $active_token2 > $canvas->yview->[1] * ($canvas->bbox("all")->[3] - $canvas->bbox("all")->[1]));
}

sub up1 {
  for (my $i = 0; $i < @id1; $i++) {
    if ($status1[$i]) {
      $id1[$i]->deselect;
      $active_token1 = $i;
    }
  }
  $active_token1-- if $active_token1 > 0;
  $id1[$active_token1]->select;
  $canvas->yviewScroll(-2 => unit) if (10 + $buff * $active_token1 < $canvas->yview->[0] * ($canvas->bbox("all")->[3] - $canvas->bbox("all")->[1]));
}

sub up2 {
  for (my $i = 0; $i < @id2; $i++) {
    if ($status2[$i]) {
      $id2[$i]->deselect;
      $active_token2 = $i;
    }
  }
  $active_token2-- if $active_token2 > 0;
  $id2[$active_token2]->select;
  $canvas->yviewScroll(-2 => unit) if (10 + $buff * $active_token2 < $canvas->yview->[0] * ($canvas->bbox("all")->[3] - $canvas->bbox("all")->[1]));
}

# This function creates a link between the pair of words following the latest
# linked pair.
sub autopair {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;

  con();
}

sub autopaircs {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1] = 1;
  $status2[$autopair_last_selected2+1] = 1;

  con();
}

sub autopairen {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2] = 1;

  con();
}

sub autopairposs {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  possible();
}

# This function creates two links, crossed.
sub autocrosspair {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+2] = 1;
  con();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2-1] = 1;
  con();
  $autopair_last_selected2++;
}

# This function creates two links to two Czech words, starting from one English
sub autoczdouble {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  con();
  $status1[$autopair_last_selected1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  con();
}

# This function creates a possible link between next English word and the next
# Czech word. Moreover a regular link between the second following English word
# and the Czech word is created.
sub autoenprep {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  possible();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2] = 1;
  con();
}
sub autoenprep2 {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  possible();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2] = 1;
  possible();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2] = 1;
  con();
}
sub auto_enprepadjnoun_czadjnoun {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+2] = 1;
  possible();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2-1] = 1;
  con();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  con();
}
sub auto_enprepadjadjnoun_czadjadjnoun {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+3] = 1;
  possible();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2-2] = 1;
  con();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  con();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+1] = 1;
  con();
}
sub auto_enthat_czcommaze {
  if (!defined $autopair_last_selected2 || !defined $autopair_last_selected1) {
    $info = "ERROR: Please use autopairing only after you have linked some words manually";
    return;
  }
  $status2[$autopair_last_selected2+1] = 1;
  nullcon();
  $status1[$autopair_last_selected1+1] = 1;
  $status2[$autopair_last_selected2+2] = 1;
  con();
}

#This function makes a connection if there is something selected from the 
#source file, as well as the target file
sub con {
    
    #clears out the old lists from past connections  

    undef @list1;
    undef @list2;
  

    #These 2 while loops get the selected elements to connect
    my $i = 0;
    while($i < @status1){
	if($status1[$i]){
	    push @list1,$i;
            $autopair_last_selected1 = $i;
	}
	$i++;
    }    
    $i = 0;
    while($i < @status2){
	if($status2[$i]){
	    push @list2,$i;
            $autopair_last_selected2 = $i;
	}
	$i++;
    }
    
    #error checking to make sure a word is selected from both lists
    if(!@list1){
	$info = "ERROR: Nothing Selected From The Source Text";
#	$entry1_w->bell();
	return;
    }
    if(!@list2){
	$info = "ERROR: Nothing Selected From The Target Text";
#	$entry1_w->bell();
	return;
    }


    #These nested for loops do the actual connecting and drawing of connections
    foreach $i (@list1){
	#clear selection in the list
#	$id1[$i]->deselect;
	
	#keep active item for easier use of arrow keys
	$active1 = $i;

	foreach $j (@list2){
	    #increment the indexes to store them in the blinker-style
	    my $temp1 = $i+1;
	    my $temp2 = $j+1;
	    
	    #clear selection in the list
#	    $id2[$j]->deselect;

	    #keep active item for easier use of arrow keys	    
	    $active2 = $j;

	    #looks through all the connections, and doesn't connect if the connection is 
	    #already there
	    my $foundflag = 0;
	    foreach(@{$blinkarray[$linenum]}){
		if($_ =~ /^$temp1 $temp2$/){
		    $foundflag = 1;
		    $info = "connection \"$whole_file1[$linenum][$i]\" to \"$whole_file2[$linenum][$j]\" has already been done";
		    last;
		}
	    }
	    foreach(@{$possiblearray[$linenum]}){
		if($_ =~ /^$temp1 $temp2$/){
		    $foundflag = 1;
		    $info = "connection \"$whole_file1[$linenum][$i]\" to \"$whole_file2[$linenum][$j]\" has already been done";
		    last;
		}
	    }
	    #skip this connection if it has already been done
	    next if($foundflag == 1);
	    
	    $id1[$temp1-1]->configure(-background, $connected);
	    $id2[$temp2-1]->configure(-background, $connected);

	    #find correct coordinates, and save indexes in blinker-style file
	    push @{$blinkarray[$linenum]}, "$temp1 $temp2";
#	    print "Connecting $linenum th sentence" . $sentence_name[1][$linenum] . " $temp1 $temp2\n";
	    my $x1 = 150;
	    my $y1 = 50 + $buff * $i;
	    my $x2 = 300;
	    my $y2 = 50 + $buff * $j;
	    
	    #keep track of lines for the undo function
	    push @lines, $canvas->createLine($x1,$y1,$x2,$y2);
	}
    }
}
#-----------------------------------------------------------------------------
#con end

#creates edge that symolize possible connection between words
sub possible {
    #clears out the old lists from past connections  

    undef @list1;
    undef @list2;
  

    #These 2 while loops get the selected elements to connect
    my $i = 0;
    while($i < @status1){
	if($status1[$i]){
	    push @list1,$i;
            $autopair_last_selected1 = $i;
	}
	$i++;
    }    
    $i = 0;
    while($i < @status2){
	if($status2[$i]){
	    push @list2,$i;
            $autopair_last_selected2 = $i;
	}
	$i++;
    }
    
    #error checking to make sure a word is selected from both lists
    if(!@list1){
	$info = "ERROR: Nothing Selected From The Source Text";
#	$entry1_w->bell();
	return;
    }
    if(!@list2){
	$info = "ERROR: Nothing Selected From The Target Text";
#	$entry1_w->bell();
	return;
    }


    #These nested for loops do the actual connecting and drawing of connections
    foreach $i (@list1){
	#clear selection in the list
#	$id1[$i]->deselect;
	
	#keep active item for easier use of arrow keys
	$active1 = $i;

	foreach $j (@list2){
	    #increment the indexes to store them in the blinker-style
	    my $temp1 = $i+1;
	    my $temp2 = $j+1;
	    
	    #clear selection in the list
#	    $id2[$j]->deselect;

	    #keep active item for easier use of arrow keys	    
	    $active2 = $j;

	    #looks through all the connections, and doesn't connect if the connection is 
	    #already there
	    my $foundflag = 0;
	    foreach(@{$blinkarray[$linenum]}){
		if($_ =~ /^$temp1 $temp2$/){
		    $foundflag = 1;
		    $info = "connection \"$whole_file1[$linenum][$i]\" to \"$whole_file2[$linenum][$j]\" has already been done";
		    last;
		}
	    }
	    foreach(@{$possiblearray[$linenum]}){
		if($_ =~ /^$temp1 $temp2$/){
		    $foundflag = 1;
		    $info = "connection \"$whole_file1[$linenum][$i]\" to \"$whole_file2[$linenum][$j]\" has already been done";
		    last;
		}
	    }
	    #skip this connection if it has already been done
	    next if($foundflag == 1);
	    
	    $id1[$temp1-1]->configure(-background, $connected);
	    $id2[$temp2-1]->configure(-background, $connected);

	    #find correct coordinates, and save indexes in blinker-style file
	    push @{$possiblearray[$linenum]}, "$temp1 $temp2";
#	    print "Connecting $linenum th sentence" . $sentence_name[1][$linenum] . " $temp1 $temp2\n";
	    my $x1 = 150;
	    my $y1 = 50 + $buff * $i;
	    my $x2 = 300;
	    my $y2 = 50 + $buff * $j;
	    
	    #keep track of lines for the undo function
	    push @lines, $canvas->createLine($x1,$y1,$x2,$y2, -fill=>$possible_color);
	}
    }

}
#----------------------------------------------------------------
#possible end

#creates edge that symolize phrasal connection between words
sub phrasal {
    #clears out the old lists from past connections  
    undef @list1;
    undef @list2;
  

    #These 2 while loops get the selected elements to connect
    my $i = 0;
    while($i < @status1){
	if($status1[$i]){
	    push @list1,$i;
	}
	$i++;
    }    
    $i = 0;
    while($i < @status2){
	if($status2[$i]){
	    push @list2,$i;
	}
	$i++;
    }
    
    #error checking to make sure a word is selected from both lists
    if(!@list1){
	$info = "ERROR: Nothing Selected From The Source Text";
#	$entry1_w->bell();
	return;
    }
    if(!@list2){
	$info = "ERROR: Nothing Selected From The Target Text";
#	$entry1_w->bell();
	return;
    }


    #These nested for loops do the actual connecting and drawing of connections
    foreach $i (@list1){
	#clear selection in the list
#	$id1[$i]->deselect;
	
	#keep active item for easier use of arrow keys
	$active1 = $i;

	foreach $j (@list2){
	    #increment the indexes to store them in the blinker-style
	    my $temp1 = $i+1;
	    my $temp2 = $j+1;
	    
	    #clear selection in the list
#	    $id2[$j]->deselect;

	    #keep active item for easier use of arrow keys	    
	    $active2 = $j;

	    #looks through all the connections, and doesn't connect if the connection is 
	    #already there
	    my $foundflag = 0;
	    foreach(@{$phrasalarray[$linenum]}){
		if($_ =~ /^$temp1 $temp2$/){
		    $foundflag = 1;
		    $info = "connection \"$whole_file1[$linenum][$i]\" to \"$whole_file2[$linenum][$j]\" has already been done";
		    last;
		}
	    }
	    #skip this connection if it has already been done
	    next if($foundflag == 1);
	    
	    $id1[$temp1-1]->configure(-background, $connected);
	    $id2[$temp2-1]->configure(-background, $connected);

	    #find correct coordinates, and save indexes in blinker-style file
	    push @{$phrasalarray[$linenum]}, "$temp1 $temp2";
#	    print "Connecting $linenum th sentence" . $sentence_name[1][$linenum] . " $temp1 $temp2\n";
	    my $x1 = 150;
	    my $y1 = 52 + $buff * $i;
	    my $x2 = 300;
	    my $y2 = 52 + $buff * $j;
	    
	    #keep track of lines for the undo function
	    push @lines, $canvas->createLine($x1,$y1,$x2,$y2, -fill=>$phrasal_color);
	}
    }

}
#possible end

# draw lines according to information in blinkarray - e.g. when moved  forwards or backwards
sub draw_lines {
# print "Redrawind connections of words... for sentence " . $sentence_name[1][$linenum] . "\n";
 # delete old lines
 foreach my $index (@{$blinkarray[$linenum]}) {
   my @tmp=split(/ /, $index);
# words are connected together, there is no null connect
   if ($tmp[0] && $tmp[1])
   {
     $id1[$tmp[0]-1]->configure(-background, $connected) if $id1[$tmp[0]-1];
     $id2[$tmp[1]-1]->configure(-background, $connected) if $id1[$tmp[1]-1];
    #find correct coordinates, and save indexes in blinker-style file
#    push @{$blinkarray[$linenum]}, "$temp1 $temp2";
#    print "Connecting $linenum th sentence" . $sentence_name[1][$linenum] . " @tmp \n";
      my $x1 = 150;
      my $y1 = 50 + $buff * ($tmp[0]-1);
      my $x2 = 300;
      my $y2 = 50 + $buff * ($tmp[1]-1);
    
    #keep track of lines for the undo function
      push @lines, $canvas->createLine($x1,$y1,$x2,$y2);
    }
    else #null connect
    {
      if ($tmp[0])  #word from first list is null connected
      {
	 $id1[$tmp[0]-1]->configure(-background, $nullback, -foreground, $nullfore,-disabledforeground,"white");
      }
      if ($tmp[1])
      {
	 $id2[$tmp[1]-1]->configure(-background, $nullback, -foreground, $nullfore,-disabledforeground,"white");
      }
    }
 }
# print "Just created @lines lines. \n";
 foreach my $index (@{$possiblearray[$linenum]}) {
   @tmp=split(/ /, $index);
# words are connected together, there is no null connect
     $id1[$tmp[0]-1]->configure(-background, $connected);
     $id2[$tmp[1]-1]->configure(-background, $connected);
    #find correct coordinates, and save indexes in blinker-style file
#    push @{$blinkarray[$linenum]}, "$temp1 $temp2";
#    print "Connecting $linenum th sentence" . $sentence_name[1][$linenum] . " @tmp \n";
      my $x1 = 150;
      my $y1 = 50 + $buff * ($tmp[0]-1);
      my $x2 = 300;
      my $y2 = 50 + $buff * ($tmp[1]-1);
    
    #keep track of lines for the undo function
      push @lines, $canvas->createLine($x1,$y1,$x2,$y2, -fill=> $possible_color);
    }
 
 foreach my $index (@{$phrasalarray[$linenum]}) {
   @tmp=split(/ /, $index);
# words are connected together, there is no null connect
     $id1[$tmp[0]-1]->configure(-background, $connected);
     $id2[$tmp[1]-1]->configure(-background, $connected);
    #find correct coordinates, and save indexes in blinker-style file
#    push @{$blinkarray[$linenum]}, "$temp1 $temp2";
#    print "Connecting $linenum th sentence" . $sentence_name[1][$linenum] . " @tmp \n";
      my $x1 = 150;
      my $y1 = 52 + $buff * ($tmp[0]-1);
      my $x2 = 300;
      my $y2 = 52 + $buff * ($tmp[1]-1);
    
    #keep track of lines for the undo function
      push @lines, $canvas->createLine($x1,$y1,$x2,$y2, -fill=> $phrasal_color);
    }
    init_selection();
}
#----------------- ------------------------------------------------------------
#draw_lines end

#This function clears the connections, but leaves the files intact
sub clear_lines{

        
    
    while(@lines){
	$canvas->delete(pop @lines);
    }

    #clear the arrays used for connections
    undef @redo;
    undef @lines;
    
    $info = "Connections Clear";
    &browse;
}
#-----------------------------------------------------------------------------
#clear_lines end


#This function clears the lists, entry widgets, and all the connections   
sub clear_tot{
    #enables the flag for the size option
    $bopenflag = 0;

    #clears out the arrays used for various purposes
    undef @blinkarray;
    undef @redo;
    undef @status1;
    undef @status2;
    undef $holdfile;
    undef $holdfileold;
    undef $holdfile2;
    undef $holdfileold2;
    undef $sentence1;
    undef $sentence2;
    
    #clears out the status of the words, and other variables to restart
    $size1 = $linenum = $linenum2 = $size2 = $active1 = $active2 = 0;

    #clears out the entry widgets
#    $entry1_w->delete(0,"end");
#    $entry2_w->delete(0,"end");

    #clears the connection lines from the canvas
    while(@lines){
	$canvas->delete(pop @lines);
    }

    #deletes the buttons from the canvas
    while(@del1){
	$canvas->delete(pop @del1);
    }
    while(@del2){
	$canvas->delete(pop @del2);
    }

    #clear source file from canvas
    while(@id1){
	$d = (pop @id1);
	$d->destroy();
    }
    #clear target file from canvas
    while(@id2){
	$d = (pop @id2);
	$d->destroy();
    }

    #undefines the id's after they have been removed from the canvas
    undef @lines;
    undef @del1;
    undef @del2;
    undef @id1;
    undef @id2;
    
    #gives the focus to the first entry widget to re-enter a file
#    $entry1_w->focus();

    #change the scroll region because new elements were inserted    
    $canvas->configure(-scrollregion,[ $canvas->bbox("all") ]);
    
    $info = "Clear Complete";
}
#-----------------------------------------------------------------------------
#clear_tot end


sub refresh {
  # redraw the screen (via a nasty hack)
  $linenum = $linenum - 1;
  $linenum2 = $linenum2 - 1;
  load_files();
}



sub OneActive_phrasal {
  my @spliceblink;
  my @save;
  for($i = 0; $i < @{$phrasalarray[$linenum]}; $i++){
#adjust to Blinker file format
    my $t1 = $list1[0]+1;
#if a match is found
    if($phrasalarray[$linenum][$i] =~ /^$t1 ./){
#save the matched connections
      push @save,$phrasalarray[$linenum][$i];
      push @spliceblink, $i;
      $counter++;
      $id1[$list1[0]]->deselect;
    }
  }
    #error checking if no connections were found to undo
  if($counter == 0){
    $info = "No connections from this word to undo";
    $id1[$list1[0]]->deselect;
    return;
  }

    #do this for eatch match
  foreach(@save){
    @temp = split / /,$_;
  #this checks the lines for the matching coordinates unless it is a null connection
    if($temp[1] != 0){
      for($l = 0; $l < @lines; $l++){
        @coors = $canvas->coords($lines[$l]);
	$one = 50 + (($temp[0]-1) * $buff);
	$three = 50 + (($temp[1]-1) * $buff);
			
  #if a matching line coordinate is found, delete the line from canvas and array
	if($coors[1] == $one && $coors[3] == $three){
          $canvas->delete($lines[$l]);
          push @splicelines,$l;
        }
      }

    }
#change the color of the selected word back to normal - no more connections to it
    $id1[$temp[0]-1]->configure(-background,$normal,-foreground,"black",-disabledforeground,"blue");
		
  }
    #delete the matching items from the blink array and lines array
  my $count = 0;
  foreach(@spliceblink){
#delete the connection from @blinkarray
    splice(@{$phrasalarray[$linenum]},$_-$count,1); 
    $count++;
  }


    #this goes through the save array again, after blinkarray has been spliced.  It looks for
    #words in the second list that no longer have connections to them, and changes the color back to normal
  foreach(@save){
    @temp = split / /, $_;
    if($temp[1] != 0){
    #check for empty word, change color back
      $flag2 = 0;
    #checks for connections to second word that was undone
        foreach $b (@{$phrasalarray[$linenum]}){
          my @tmp = split / /,$b;
          $flag2++ if($tmp[1] == $temp[1]);
        }
	 #if there are no more connections to the words, then change color back to normal
        $id2[$temp[1]-1]->configure(-background,$normal) if($flag2 == 0);
     }
  }
  $count = 0;
  foreach(@splicelines){
    #delete the connection from the lines array
    splice(@lines,$_-$count,1);
    $count++;
  }
  refresh();	    
    #does this if no connection was found to undo
  if(@{$phrasalarray[$linenum]} == $blinkerlen){
    #unselect the selected items
    $id1[$list1[0]]->deselect;
    $info = "No connection found to undo";
    return;
  }
}



sub OneActive_possible {
  my @spliceblink;
  my @save;
  for($i = 0; $i < @{$possiblearray[$linenum]}; $i++){
#adjust to Blinker file format
    my $t1 = $list1[0]+1;
#if a match is found
    if($possiblearray[$linenum][$i] =~ /^$t1 ./){
#save the matched connections
      push @save,$possiblearray[$linenum][$i];
      push @spliceblink, $i;
      $counter++;
      $id1[$list1[0]]->deselect;
    }
  }
    #error checking if no connections were found to undo
  if($counter == 0){
    $info = "No connections from this word to undo";
    $id1[$list1[0]]->deselect;
    return;
  }

    #do this for eatch match
  foreach(@save){
    @temp = split / /,$_;
  #this checks the lines for the matching coordinates unless it is a null connection
    if($temp[1] != 0){
      for($l = 0; $l < @lines; $l++){
        @coors = $canvas->coords($lines[$l]);
	$one = 50 + (($temp[0]-1) * $buff);
	$three = 50 + (($temp[1]-1) * $buff);
			
  #if a matching line coordinate is found, delete the line from canvas and array
	if($coors[1] == $one && $coors[3] == $three){
          $canvas->delete($lines[$l]);
          push @splicelines,$l;
        }
      }

    }
#change the color of the selected word back to normal - no more connections to it
    $id1[$temp[0]-1]->configure(-background,$normal,-foreground,"black",-disabledforeground,"blue");
		
  }
    #delete the matching items from the blink array and lines array
  my $count = 0;
  foreach(@spliceblink){
#delete the connection from @blinkarray
    splice(@{$possiblearray[$linenum]},$_-$count,1); 
    $count++;
  }


    #this goes through the save array again, after blinkarray has been spliced.  It looks for
    #words in the second list that no longer have connections to them, and changes the color back to normal
  foreach(@save){
    @temp = split / /, $_;
    if($temp[1] != 0){
    #check for empty word, change color back
      $flag2 = 0;
    #checks for connections to second word that was undone
        foreach $b (@{$possiblearray[$linenum]}){
          my @tmp = split / /,$b;
          $flag2++ if($tmp[1] == $temp[1]);
        }
	 #if there are no more connections to the words, then change color back to normal
        $id2[$temp[1]-1]->configure(-background,$normal) if($flag2 == 0);
     }
  }
  $count = 0;
  foreach(@splicelines){
    #delete the connection from the lines array
    splice(@lines,$_-$count,1);
    $count++;
  }
    #does this if no connection was found to undo
  if(@{$possiblearray[$linenum]} == $blinkerlen){
    #unselect the selected items
    $id1[$list1[0]]->deselect;
    $info = "No connection found to undo";
    return;
  }
	    
}

sub SecondActiv_phrasal {
  my @save;
  my @spliceblink;
  for($i = 0; $i < @{$phrasalarray[$linenum]}; $i++){
#adjust to Blinker file format
    my $t2 = $list2[0]+1;

#if a match is found
    if($phrasalarray[$linenum][$i] =~ /. $t2$/){

    #save the matched connections
      push @save,$phrasalarray[$linenum][$i];
      push @spliceblink, $i;
      $counter++;
      $id2[$list2[0]]->deselect;
    }
  }
    #error checking if no connections were found to undo
  if($counter == 0){
    $info = "No connections from this word to undo";
    $id2[$list2[0]]->deselect;
    return;
  }

    #do this for each match
  foreach(@save){
    my @temp = split / /,$_;

  #this checks the lines for the matching coordinates unless it is a null connection
    if($temp[0] != 0){
      for($l = 0; $l < @lines; $l++){
        @coors = $canvas->coords($lines[$l]);
        $one = 50 + (($temp[0]-1) * $buff);
        $three = 50 + (($temp[1]-1) * $buff);
		
 	#if a matching line coordinate is found, delete the line from canvas and array
        if($coors[1] == $one && $coors[3] == $three){
          $canvas->delete($lines[$l]);
          push @splicelines,$l;
        }
      }
    }
#change the selected word back to normal
    $id2[$temp[1]-1]->configure(-background,$normal,-foreground,"black",-disabledforeground,"blue");

  }

    #delete the matching items from the blink array and lines array
  my $count = 0;
  foreach(@spliceblink){
  #delete the connection from @phrasalarray
    splice(@{$phrasalarray[$linenum]},$_-$count,1); 
    $count++;
  }

    #this goes through the save array again, after phrasalarray has been spliced.  It looks for
    #words in the first list that no longer have connections to them, and changes the color back to normal
  foreach(@save){
    @temp = split / /, $_;
    if($temp[0] != 0){
    #check for empty word, change color back
      $flag1 = 0;
    #checks for connections to first word that was undone
      foreach $b (@{$phrasalarray[$linenum]}){
        my @tmp = split / /,$b;
        $flag1++ if($tmp[0] == $temp[0]);
      }
	    #if there are no more connections to the words, then change color back to normal
      $id1[$temp[0]-1]->configure(-background,$normal) if($flag1 == 0);
    }
  }

  $count = 0;
  foreach(@splicelines){
#delete the connection from the lines array
    splice(@lines,$_-$count,1);
    $count++;
  }
    #does this if no connection was found to undo
  if(@{$phrasalarray[$linenum]} == $blinkerlen){
    #unselect the selected items
    $id2[$list2[0]]->deselect;
    $info = "No connection found to undo";
    return;
  }
}



sub SecondActiv_possible {
  my @save;
  my @spliceblink;
  for($i = 0; $i < @{$possiblearray[$linenum]}; $i++){
#adjust to Blinker file format
    my $t2 = $list2[0]+1;

#if a match is found
    if($possiblearray[$linenum][$i] =~ /. $t2$/){

    #save the matched connections
      push @save,$possiblearray[$linenum][$i];
      push @spliceblink, $i;
      $counter++;
      $id2[$list2[0]]->deselect;
    }
  }
    #error checking if no connections were found to undo
  if($counter == 0){
    $info = "No connections from this word to undo";
    $id2[$list2[0]]->deselect;
    return;
  }

    #do this for each match
  foreach(@save){
    my @temp = split / /,$_;

  #this checks the lines for the matching coordinates unless it is a null connection
    if($temp[0] != 0){
      for($l = 0; $l < @lines; $l++){
        @coors = $canvas->coords($lines[$l]);
        $one = 50 + (($temp[0]-1) * $buff);
        $three = 50 + (($temp[1]-1) * $buff);
		
 	#if a matching line coordinate is found, delete the line from canvas and array
        if($coors[1] == $one && $coors[3] == $three){
          $canvas->delete($lines[$l]);
          push @splicelines,$l;
        }
      }
    }
#change the selected word back to normal
    $id2[$temp[1]-1]->configure(-background,$normal,-foreground,"black",-disabledforeground,"blue");

  }

    #delete the matching items from the blink array and lines array
  my $count = 0;
  foreach(@spliceblink){
  #delete the connection from @possiblearray
    splice(@{$possiblearray[$linenum]},$_-$count,1); 
    $count++;
  }

    #this goes through the save array again, after possiblearray has been spliced.  It looks for
    #words in the first list that no longer have connections to them, and changes the color back to normal
  foreach(@save){
    @temp = split / /, $_;
    if($temp[0] != 0){
    #check for empty word, change color back
      $flag1 = 0;
    #checks for connections to first word that was undone
      foreach $b (@{$possiblearray[$linenum]}){
        my @tmp = split / /,$b;
        $flag1++ if($tmp[0] == $temp[0]);
      }
	    #if there are no more connections to the words, then change color back to normal
      $id1[$temp[0]-1]->configure(-background,$normal) if($flag1 == 0);
    }
  }

  $count = 0;
  foreach(@splicelines){
#delete the connection from the lines array
    splice(@lines,$_-$count,1);
    $count++;
  }
    #does this if no connection was found to undo
  if(@{$possiblearray[$linenum]} == $blinkerlen){
    #unselect the selected items
    $id2[$list2[0]]->deselect;
    $info = "No connection found to undo";
    return;
  }
}



#This function undoes a connection, which can be done in 3 different ways (See README)
sub undo{
    #checks if there is a connection to undo
    if(!@{$blinkarray[$linenum]} && !@{$possiblearray[$linenum]} && !@{$phrasalarray[$linenum]}){
	$info = "No Connections to Undo";
	$entry1_w->bell();
	return;
    }

    #clear out old lists from this function
    undef @list1;
    undef @list2;
    undef @splicelines;
    undef @spliceblink;
    undef @save;

    #These 2 while loops get the selected elements to undo
    my $i = 0;
    while($i < @status1){
	if($status1[$i]){
	    push @list1,$i;
	}
	$i++;
    }    
    $i = 0;
    while($i < @status2){
	if($status2[$i]){
	    push @list2,$i;
	}
	$i++;
    }


    #checks for no selected items
    if(!@list1 && !@list2){
      $info = "No selected items to disconnect";
      return;
    }

    #does this if there are selected items to undo 
    elsif(@list1 || @list2){

	#checks the length of @blinkarray to compare later to see if something was undone or not
	my $blinkerlen = @{$blinkarray[$linenum]};

	#error checking to see if there is 1 word selected from each file
	if(@list1 > 1 ||  @list2 > 1){
	    $info = "Please select only one word to disconnect at a time";
	    return;
	}
	
	#does this if an item is selected from list 1 and 2
	if(@list1 == 1 && @list2 == 1){
	    #this for looip looks through each connection, looking for a match of the selected items
#	    print "There are two words to disconnect... $list1[0] and $list2[0]\n";
	    for($i = 0; $i < @{$blinkarray[$linenum]}; $i++){

		#must match the index with the blinkarray style indexes
		my $t1 = $list1[0]+1;
		my $t2 = $list2[0]+1;

		#look for a match in the @blinkarray(list of connections)
		if($blinkarray[$linenum][$i] =~ /^$t1 $t2$/){
		    #delete the connection from @blinkarray
		    splice(@{$blinkarray[$linenum]},$i,1);
		    
		    #unselect the selected items
#		    $id1[$list1[0]]->deselect;
#		    $id2[$list2[0]]->deselect;
		    
		    #check for empty word, change color back
		    $flag1 = $flag2 = 0;
		    #checks for connections to either word that was undone
		    foreach(@{$blinkarray[$linenum]}) {
			my @tmp = split / /,$_;
			$flag1++ if($tmp[0]-1 == $list1[0]);
			$flag2++ if($tmp[1]-1 == $list2[0]);
		    }
		    #if there are no more connections to the words, then change color back to normal
		    $id1[$list1[0]]->configure(-background,$normal) if($flag1 == 0);
		    $id2[$list2[0]]->configure(-background,$normal) if($flag2 == 0);
		    
		    #this checks the lines for the matching coordinates 
		    for($l = 0; $l < @lines; $l++){
			@coors = $canvas->coords($lines[$l]);
			$one = 50 + ($list1[0] * $buff);
			$three = 50 + ($list2[0] * $buff);
#			print "Searching for coordinates... for line $one and $three";
#			print "  we have $coors[1] and $coors[3] \n";

			#if a matching line coordinate is found, delete the line from canvas and array
			if($coors[1] == $one && $coors[3] == $three){
			    
#			    print "Line found! \n";
			    $canvas->delete($lines[$l]);
			    splice(@lines,$l,1);
			    last;
			}
		    }
		    last;
		}
	    }
	    for($i = 0; $i < @{$possiblearray[$linenum]}; $i++){

		#must match the index with the blinkarray style indexes
		my $t1 = $list1[0]+1;
		my $t2 = $list2[0]+1;

		#look for a match in the @blinkarray(list of connections)
		if($possiblearray[$linenum][$i] =~ /^$t1 $t2$/){
		    #delete the connection from @blinkarray
		    splice(@{$possiblearray[$linenum]},$i,1);
		    
		    #unselect the selected items
#		    $id1[$list1[0]]->deselect;
#		    $id2[$list2[0]]->deselect;
		    
		    #check for empty word, change color back
		    $flag1 = $flag2 = 0;
		    #checks for connections to either word that was undone
		    foreach(@{$possiblearray[$linenum]}) {
			my @tmp = split / /,$_;
			$flag1++ if($tmp[0]-1 == $list1[0]);
			$flag2++ if($tmp[1]-1 == $list2[0]);
		    }
		    #if there are no more connections to the words, then change color back to normal
		    $id1[$list1[0]]->configure(-background,$normal) if($flag1 == 0);
		    $id2[$list2[0]]->configure(-background,$normal) if($flag2 == 0);
		    
		    #this checks the lines for the matching coordinates 
		    for($l = 0; $l < @lines; $l++){
			@coors = $canvas->coords($lines[$l]);
			$one = 50 + ($list1[0] * $buff);
			$three = 50 + ($list2[0] * $buff);
#			print "Searching for coordinates... for line $one and $three";
#			print "  we have $coors[1] and $coors[3] \n";

			#if a matching line coordinate is found, delete the line from canvas and array
			if($coors[1] == $one && $coors[3] == $three){
			    
#			    print "Line found! \n";
			    $canvas->delete($lines[$l]);
			    splice(@lines,$l,1);
			    last;
			}
		    }
		    last;
		}
	    }
	    for($i = 0; $i < @{$phrasalarray[$linenum]}; $i++){

		#must match the index with the blinkarray style indexes
		my $t1 = $list1[0]+1;
		my $t2 = $list2[0]+1;

		#look for a match in the @blinkarray(list of connections)
		if($phrasalarray[$linenum][$i] =~ /^$t1 $t2$/){
		    #delete the connection from @blinkarray
		    splice(@{$phrasalarray[$linenum]},$i,1);
		    
		    #unselect the selected items
#		    $id1[$list1[0]]->deselect;
#		    $id2[$list2[0]]->deselect;
		    
		    #check for empty word, change color back
		    $flag1 = $flag2 = 0;
		    #checks for connections to either word that was undone
		    foreach(@{$phrasalarray[$linenum]}) {
			my @tmp = split / /,$_;
			$flag1++ if($tmp[0]-1 == $list1[0]);
			$flag2++ if($tmp[1]-1 == $list2[0]);
		    }
		    #if there are no more connections to the words, then change color back to normal
		    $id1[$list1[0]]->configure(-background,$normal) if($flag1 == 0);
		    $id2[$list2[0]]->configure(-background,$normal) if($flag2 == 0);
		    
		    #this checks the lines for the matching coordinates 
		    for($l = 0; $l < @lines; $l++){
			@coors = $canvas->coords($lines[$l]);
			$one = 52 + ($list1[0] * $buff);
			$three = 52 + ($list2[0] * $buff);
			#if a matching line coordinate is found, delete the line from canvas and array
#			if($coors[1] == $one && $coors[3] == $three ){
			if($coors[1] > $one-2 && $coors[1] < $one+2 && $coors[3] > $three-2 && $coors[3] < $three+2){
			    
#			    print "Line found! \n";
			    $canvas->delete($lines[$l]);
			    splice(@lines,$l,1);
			    last;
			}
		    }
#                    refresh();
#		    last;
		}
	    }
	}

	#does this if an item is selected from list 1 but not list 2
	elsif(@list1 == 1 && @list2 == 0){
	    
	     OneActive_phrasal();
	     OneActive_possible();
	     #looks for connections to the element selected in list1
	    for($i = 0; $i < @{$blinkarray[$linenum]}; $i++){
		#adjust to Blinker file format
		my $t1 = $list1[0]+1;
		
		#if a match is found
		if($blinkarray[$linenum][$i] =~ /^$t1 ./){

		    #save the matched connections
		    push @save,$blinkarray[$linenum][$i];
		    push @spliceblink, $i;
		    $counter++;
		    $id1[$list1[0]]->deselect;
		}
	    }
	    #error checking if no connections were found to undo
	    if($counter == 0){
		$info = "No connections from this word to undo";
		$id1[$list1[0]]->deselect;
		return;
	    }

	    #do this for eatch match
	    foreach(@save){
		@temp = split / /,$_;
		#this checks the lines for the matching coordinates unless it is a null connection
		if($temp[1] != 0){
		    for($l = 0; $l < @lines; $l++){
			@coors = $canvas->coords($lines[$l]);
			$one = 50 + (($temp[0]-1) * $buff);
			$three = 50 + (($temp[1]-1) * $buff);
			
			#if a matching line coordinate is found, delete the line from canvas and array
			if($coors[1] == $one && $coors[3] == $three){
			    $canvas->delete($lines[$l]);
			    push @splicelines,$l;
			}
		    }

		}
		#change the color of the selected word back to normal - no more connections to it
		$id1[$temp[0]-1]->configure(-background,$normal,-foreground,"black",-disabledforeground,"blue");
		
	    }
	    #delete the matching items from the blink array and lines array
	    my $count = 0;
	    foreach(@spliceblink){
		#delete the connection from @blinkarray
		splice(@{$blinkarray[$linenum]},$_-$count,1); 
		$count++;
	    }


	    #this goes through the save array again, after blinkarray has been spliced.  It looks for
	    #words in the second list that no longer have connections to them, and changes the color back to normal
	    foreach(@save){
		@temp = split / /, $_;
		if($temp[1] != 0){
		    #check for empty word, change color back
		    $flag2 = 0;
		    #checks for connections to second word that was undone
		    foreach $b (@{$blinkarray[$linenum]}){
			my @tmp = split / /,$b;
			$flag2++ if($tmp[1] == $temp[1]);
		    }
		    #if there are no more connections to the words, then change color back to normal
		    $id2[$temp[1]-1]->configure(-background,$normal) if($flag2 == 0);
		}
	    }

	    $count = 0;
	    foreach(@splicelines){
		#delete the connection from the lines array
		splice(@lines,$_-$count,1);
		$count++;
	    }
	    #does this if no connection was found to undo
	    if(@{$blinkarray[$linenum]} == $blinkerlen){
		#unselect the selected items
		$id1[$list1[0]]->deselect;
		$info = "No connection found to undo";
		return;
	    }
	    
	}
	
	#does this if there is something selected from list 2, but not list 1
	elsif(@list1 == 0 && @list2 == 1){
            SecondActiv_phrasal;
            SecondActiv_possible;
#	    refresh;
	    for($i = 0; $i < @{$blinkarray[$linenum]}; $i++){
		#adjust to Blinker file format
		my $t2 = $list2[0]+1;

		#if a match is found
		if($blinkarray[$linenum][$i] =~ /. $t2$/){

		    #save the matched connections
		    push @save,$blinkarray[$linenum][$i];
		    push @spliceblink, $i;
		    $counter++;
		    $id2[$list2[0]]->deselect;
		}
	    }
	    #error checking if no connections were found to undo
	    if($counter == 0){
		$info = "No connections from this word to undo";
		$id2[$list2[0]]->deselect;
		return;
	    }

	    #do this for each match
	    foreach(@save){
		my @temp = split / /,$_;

		#this checks the lines for the matching coordinates unless it is a null connection
		if($temp[0] != 0){
		    for($l = 0; $l < @lines; $l++){
			@coors = $canvas->coords($lines[$l]);
			$one = 50 + (($temp[0]-1) * $buff);
			$three = 50 + (($temp[1]-1) * $buff);
			
			#if a matching line coordinate is found, delete the line from canvas and array
			if($coors[1] == $one && $coors[3] == $three){
			    $canvas->delete($lines[$l]);
			    push @splicelines,$l;
			}
		    }
		}
		#change the selected word back to normal
		$id2[$temp[1]-1]->configure(-background,$normal,-foreground,"black",-disabledforeground,"blue");
		
	    }

	    #delete the matching items from the blink array and lines array
	    my $count = 0;
	    foreach(@spliceblink){
		#delete the connection from @blinkarray
		splice(@{$blinkarray[$linenum]},$_-$count,1); 
		$count++;
	    }

	    #this goes through the save array again, after blinkarray has been spliced.  It looks for
	    #words in the first list that no longer have connections to them, and changes the color back to normal
	    foreach(@save){
		@temp = split / /, $_;
		if($temp[0] != 0){
		    #check for empty word, change color back
		    $flag1 = 0;
		    #checks for connections to first word that was undone
		    foreach $b (@{$blinkarray[$linenum]}){
			my @tmp = split / /,$b;
			$flag1++ if($tmp[0] == $temp[0]);
		    }
		    #if there are no more connections to the words, then change color back to normal
		    $id1[$temp[0]-1]->configure(-background,$normal) if($flag1 == 0);
		}
	    }


	    $count = 0;
	    foreach(@splicelines){
		#delete the connection from the lines array
		splice(@lines,$_-$count,1);
		$count++;
	    }
	    #does this if no connection was found to undo
	    if(@{$blinkarray[$linenum]} == $blinkerlen){
		#unselect the selected items
		$id2[$list2[0]]->deselect;
		$info = "No connection found to undo";
		return;
	    }
	}
    }
    
    $info = "Connection Undone";
#    refresh();
}
#-----------------------------------------------------------------------------
#undo end



#This function makes a pop-up button when the help menu option is used.
#It displays the README, which is the best help users can find.
sub help_pop{
    #make a toplevel widget
    my $t1 = $mw->Toplevel();
    #withdraw to use a different pop-up method
    $t1->withdraw;
    $t1->title("Help");
    $f = $t1->Frame->pack(-side,'bottom');
    $help = $t1->Scrolled("Text",-background,'white',
			  -selectbackground,'blue',
			  -selectforeground,'white')->pack(-expand, 1, -fill,'both');
    
    
    #error checking for opening the README file
    if(!open(FH, "README.txt")){
	$info = "Error opening 'README.txt'";
	$t1->withdraw;
	$entry1_w->bell();
	return(-1);
    }

    #inserts the README into the text file
    while(<FH>){
	$help->insert("end",$_);
    }

    #disables the text widget for read-only access
    $help->configure(-state,'disabled');    
    
    #makes a button to close the window
    $f->Button(-text,"Close",-background,"black",-foreground,"white",-command,sub{$t1->withdraw})->pack(-side,'bottom',
													-expand,1,
													-fill,'x');
   
    #makes the pop-up button appear
    $t1->Popup;
    $t1->focus();

}
#-----------------------------------------------------------------------------
#help_pop end


#This function makes a pop-up for the keyboard shortcut information
sub kbd_pop{
    #make a toplevel widget
    my $t2 = $mw->Toplevel();
    #withdraw to use a different pop-up method 
    $t2->withdraw();
    $t2->title("Keyboard Shortcuts");
    
    #makes the label with the keyboard shortcut information
    $t2->Label(-text,"The following are keyboard shortcuts when the lists have focus:\n\nKey: (depends on the mouse):\nBoth Mouse Buttons or Right Mouse Button-->Makes a connection with the selected words\nKey: Ctrl+c-->Makes a connection with the selected words\nKey: Ctrl+n-->Makes a null connection\nKey: Ctrl+u-->Undoes the last connection\nKey: Ctrl+r-->Redoes the last undone connection\nKey: spacebar-->Selects the underlined item if the mouse is not used\nKey: Ctrl+s-->Saves the Alpaco file\nKey: Ctrl+o-->Opens an Alpaco file")->pack(-side,'top');

   
    #makes the button to close the window
    $t2->Button(-text,"Close",-background,"black",-foreground,"white",-command,sub{$t2->withdraw})->pack(-side,'bottom',
													 -expand,1,
													 -fill,'x');
    
    #makes the pop-up button appear
    $t2->Popup;
    $t2->focus();
    
}
#-----------------------------------------------------------------------------
#kbd_pop end


#This function makes a pop-up for the 'about' information
sub about_pop{
    #makes a toplevel widget
    my $t3 = $mw->Toplevel();
    #withdraw to use a different pop-up method
    $t3->withdraw();
    $t3->title("About");
    
    #makes a frame widget
    $fr = $t3->Frame->pack(-side,'bottom');
    #makes a text widget for the about information
    $about = $t3->Text(
		       -selectbackground,'blue',
		       -selectforeground,'white')->pack(-expand,1,-fill,'both');

    #inserts the necessary information
    $about->insert("end","Alpaco (Aligner for Parallel Corpora)\n\n");
    $about->insert("end","Version 1.0\n\n");
    $about->insert("end","Research project by Dr. Ted Pedersen and Brian Rassier\n\n");
    $about->insert("end","This program is free software; you can redistribute it and/or\nmodify it under the terms of the GNU General Public License\nas published by the Free Software Foundation; either version 2\nof the License, or (at your option) any later version.\nThis program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\nGNU General Public License for more details\n");
    
    
    #makes a button to close the window
    $fr->Button(-text,"Close",-background,"black",-foreground,"white",-command,sub{$t3->withdraw})->pack(-side,'bottom',
													-expand,1,
													 -fill,'x');
													 
    #disables the text widget for read-only access						 
    $about->configure(-state,'disabled');    		
											     
    #makes the pop-up button appear
    $t3->Popup;
    $t3->focus();

   
}
#-----------------------------------------------------------------------------
#about_pop end


#This function function makes a pop-up for the open Alpaco file 
sub open_pop{
    
    #makes a toplevel widget with entry widget and open/cancel buttons
    $t4 = $mw->Toplevel();
    #withdraw for use of a different pop-up method
    $t4->withdraw();
    $t4->title("Open Alpaco");
    $t4->Label(-text,"Open Filename:")->pack(-side,'top');
    $e = $t4->Entry(-textvariable,\$open,-background,"white",-takefocus,1)->pack(-side,'top',-anchor,'w');
    
    $frame = $t4->Frame->pack(-side,'bottom');
    $frame->Button(-text,"Open",-background,"black",-foreground,"white",-command,\&open2)->pack(-side,'left',padx,5);
    $frame->Button(-text,"Cancel",-background,"black",-foreground,"white",-command,sub{$t4->withdraw})->pack(-side,'left');

    
    #makes the find button that will help find an alpaco file
    $frame->Button(-text,"Find Alpaco File", -background,"black",-foreground,"white",-command,\&find_al)->pack(-side,'bottom',-padx,25);


    #define hard-enter callback for entry one
    $e->bind("<Return>",\&open2);
    
    #makes the pop-up button appear
    $t4->Popup;
    $t4->focus();

    #gives the entry widget the focus to start with
    $e->focus();
       
}
#-----------------------------------------------------------------------------
#open_pop end




#This function makes a pop-up for the save Alpaco file
sub save_pop{
    #makes a toplevel widget with entry widget and save/cancel buttons
    $t5 = $mw->Toplevel();
    #withdraw to use a different popup method
    $t5->withdraw();
    $t5->title("Save Alpaco");
    $t5->Label(-text,"Save Filename:")->pack(-side,'top');
    $e = $t5->Entry(-textvariable,\$save,-background,"white",-takefocus,1)->pack(-side,'top',-anchor,'w');
    $t5->Button(-text,"Cancel",-background,"black",-foreground,"white",-command,sub{$t5->withdraw})->pack(-side,'bottom');
    $b = $t5->Button(-text,"Save",-background,"black",-foreground,"white",-command,\&save2)->pack(-side,'bottom');
    
    
    #define enter callback for entry one
    $e->bind("<Return>",sub{save2(); });
    
    #makes the pop-up button appear
    $t5->Popup;
    $t5->focus();

    #gives the entry widget the keyboard focus to start with
    $e->focus();

}
#-----------------------------------------------------------------------------
#save_pop end


#subfunction that is called if a file is to be saved-called by save_pop and others
sub save2{
    my $save=$file;
    print "Saving results to file $save \n";
    #error checking to check for files
    if(!$save){
	$info = "Error: Please enter a filename to save to";
#	$entry1_w->bell();
	return(-1);
    }

#CHECK IF THE FILE EXISTS HERE BEFORE OPENING $save
#IF IT ALREADY EXISTS, SEND TO GENERIC "IS THIS OK" POP UP

    if(!open(FH, ">:encoding(utf-8)", "$save")){
	$info = "Error opening '$save'";
#	$entry1_w->bell();
	return(-1);
    }
    
    my $i=1;
#    print "<s id=" . $sentence_name[1][$i] . "> <s id=" . $sentence_name[2][$i] . ">\n";
    print FH "<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n";
    print FH "<sentences>\n";
    while ($sentence_name[1][$i])
    {
      print FH "<s id=\"" . $sentence_name[1][$i] . "\">\n";
      print FH "  <english>" . join(" ", @{$whole_file1[$i]}) . "</english>\n";
      print FH "  <czech>" . join(" ", @{$whole_file2[$i]}) . "</czech>\n";
      
      my $english_count = scalar @{$whole_file1[$i]};
      my $czech_count = scalar @{$whole_file2[$i]};
     
      my $outprnt = "";
      foreach(@{$blinkarray[$i]}) {
        if ($_ =~ /(\d*) (\d*)/) {
          if ($1 > $english_count or $2 > $czech_count) { print STDERR "Warning: connection out of bounds.\n"; }
	      else { $outprnt .= " $1-$2"; }
        }
      }
      $outprnt =~ s/^ //;
      print FH "  <sure>$outprnt</sure>\n";
      $outprnt = "";
      foreach(@{$possiblearray[$i]}) {
        if ($_ =~ /(\d*) (\d*)/) {
          if ($1 > $english_count or $2 > $czech_count) { print STDERR "Warning: connection out of bounds.\n"; }
	      else { $outprnt .= " $1-$2"; }
        }
      }
      $outprnt =~ s/^ //;
      print FH "  <possible>$outprnt</possible>\n";
      $outprnt = "";
      foreach(@{$phrasalarray[$i]}) {
        if ($_ =~ /(\d*) (\d*)/) {
          if ($1 > $english_count or $2 > $czech_count) { print STDERR "Warning: connection out of bounds.\n"; }
	      else { $outprnt .= " $1-$2"; }
        }
      }
      $outprnt =~ s/^ //;
      print FH "  <phrasal>$outprnt</phrasal>\n";
      print FH "</s>\n";
      $i++;
    } 
    print FH "</sentences>\n";
    close(FH);
    $t5->withdraw if (Exists($t5));
}
#-----------------------------------------------------------------------------
#save2 end


#This function makes a pop-up if users try to save over a file that 
#already exists
sub file_exists{
    #get the file that was passed in as a parameter
    my $the_file = shift;

    #makes a toplevel widget with entry widget and save/cancel buttons
    $exists_pop = $mw->Toplevel();
    #withdraw to use a different popup method
    $exists_pop->withdraw();
    $exists_pop->title("Save over file?");
    $exists_pop->Label(-text,"$the_file already exists.  Continue and save over it?")->pack(-side,'top');

    $exists_pop->Button(-text,"Cancel",-background,"black",-foreground,"white",-command,sub{$exists_pop->withdraw; $OK = 0; return;})->pack(-side,'bottom');
    $exists_pop->Button(-text,"OK",-background,"black",-foreground,"white",-command,sub{$exists_pop->withdraw; $OK = 1; return;})->pack(-side,'bottom');
    
    #makes the pop-up button appear
    $exists_pop->Popup;
    $exists_pop->focus();

	}	    
#-----------------------------------------------------------------------------
#file_exists end


#This function will change the space (vertically) between the words on the canvas 
sub resize {
    #disables the resize option if no files have been opened
    if($bopenflag == -1){
	$info = "ERROR: Can't resize unless 2 files have been opened";
	$entry1_w->bell();
	return;
    }

    #don't allow resize in line-by-line mode. Naming scheme gets complicated & the line number gets off
    if($cb_value){
	$info = "Can not resize in line-by-line raw text mode";
	$entry1_w->bell();
	return;
    }

    #finds which button was pressed (+ or -)
    my $who = $sizeframe->focusCurrent();
    
    #gets the text inside the button that was pressed
    my $txt = $who->cget(-text);

    #changes the buffer depending on which button was pressed
    $buff += 5 if($txt =~ /\+/);
    $buff -= 5 if($txt =~ /-/);

    #saves the file that is being worked with as "sizetemp"
    my $temp_file_1 = $file1;
    my $temp_file_2 = $file2;

    $everse = "SizeVerse1";
    $fverse = "SizeVerse2";
    $conn = "sizetemp";
    #call save blinker function
    &saveb;
    #save the redo array
    @tempredo = @redo;


    #reopens the file "sizetemp", which will now have the new buffer size
    $open = "sizetemp";
    &open2;

    #restore the old values before the resize
    $file1 = $temp_file_1;
    $file2 = $temp_file_2;
    $everse = $file1;
    $fverse = $file2;

    #reload the redo array
    @redo = @tempredo;
    
    $info = "resize complete";
}
#-----------------------------------------------------------------------------
#resize end


#This function moves from browse mode to edit mode
sub browse{
    #if in browse mode, disable all the word buttons
    if($rb_value eq 'Browse'){
	foreach(@id1){
	    $_->configure(-state,'disabled');
	}
	foreach(@id2){
	    $_->configure(-state,'disabled');
	}
    }
    #if in edit mode, enable all word buttons
    elsif($rb_value eq 'Edit'){
	foreach(@id1){
	    $_->configure(-state,'normal');
	}
	foreach(@id2){
	    $_->configure(-state,'normal');
	}
    }
}
#-----------------------------------------------------------------------------
#browse end


#This function goes to the next/previous blinker file
sub next{

    #finds which button was pressed (Prev or Next)
    my $who = $sizeframe->focusCurrent();
    
    #gets the text inside the button that was pressed
    my $txt = $who->cget(-text);    

    #if the user hit the next button
    if($txt =~ /Next/){
	#checks if there was a blinker file opened yet, if not, opens the first one
	if($blinkfile !~ /.*A[0-9]+.samp[0-9]+\.SentPair[0-9]+/){
	    $info = "No Blinker files in the history";
	    $entry1_w->bell();
	    return;
	}
	else{
	    #gets the necessary numbers from the last blinker file
	    my $A = my $samp = my $SentPair = my $temp3 = my $temp4 = $blinkfile;
	    $A =~ s/.*A([0-9]+).+/$1/; #gets the annotator number
	    $samp =~ s/.*A[0-9]+.samp([0-9]+).+/$1/; #gets the samp#
	    $SentPair =~ s/.*A[0-9]+.samp[0-9]+\.SentPair([0-9]+).*/$1/; #gets the SentPair#
	    $temp3 =~ s/^(.*)A[0-9]+.+/$1/; #this is the beginning part of the directory
	    $temp4 =~ s/^.*SentPair[0-9]+(.*)/$1/;  #checks for anything after the SentPair (.open etc)
	    

	    #Checks for the extreme cases
	    if($SentPair == $v-1){
		#if samp# is at its limit
		if($samp == $sam){
		    #if annotator is at its limit
		    if($A == $an){
			#wrap arround if last file
			$A = 1;
		    }
		    else{
			$A++;
		    }
		    #wrap around
		    $samp = 1;
		    $SentPair = 0;
		    
		    #set $sent to the new file
		    $blinkfile = $sent = $temp3."A".$A."/samp".$samp.".SentPair".$SentPair.$temp4;
		    
		    #Check if there is an annotator for this file
		    if(!open(TEST, $sent)){
			$info = "Error opening $sent, No annotator for this file";
			$entry1_w->bell();
			return(-1);
		    }
		    close (TEST);
		    
		    #load the next file if possible
		    &openb;
		    $info = $sent." Loaded";
		    return;
		}
		#else not a total extreme case, but adjust for SentPair extreme
		else{
		    #increment samp#, wrap around SentPair#
		    $samp++;
		    $SentPair = 0;

		    #set $sent to the new file
		    $blinkfile = $sent = $temp3."A".$A."/samp".$samp.".SentPair".$SentPair.$temp4;
		    
		    #Check if there is an annotator for this file
		    if(!open(TEST, $sent)){
			$info = "Error opening $sent, No annotator for this file";
			$entry1_w->bell();
			return(-1);
		    }
		    close (TEST);

		    #load the next file if possible
		    &openb;
		    $info = $sent." Loaded";
		    return;
		}
	    }
	    #else not an extreme case at all, just increment the SentPair
	    elsif($SentPair < $v-1 ){
		$SentPair++;

		#set $sent to the new file
		$blinkfile = $sent = $temp3."A".$A."/samp".$samp.".SentPair".$SentPair.$temp4;
		
		#Check if there is an annotator for this file
		if(!open(TEST, $sent)){
		    $info = "Error opening $sent, No annotator for this file";
		    $entry1_w->bell();
		    return(-1);
		}
		close (TEST);
		
		#load the next file if possible
		&openb;
		$info = $sent." Loaded";
		return;
	    }
	}
	    
    }

    #Else the user hit the previous button, not next
    elsif($txt =~ /Prev/){
	#check if there was a blinker file opened yet
	if($blinkfile !~ /.*A[0-9]+.samp[0-9]+\.SentPair[0-9]+/){
	    $info = "No Blinker files in the history";
	    $entry1_w->bell();
	    return;
	}
	#if a blinker file was opened
	else{
	    #get the necessary numbers from the last opened blinker file
	    my $A = my $samp = my $SentPair = $temp3 = $temp4 = $blinkfile;
	    $A =~ s/.*A([0-9]+).+/$1/; #gets the annotator number
	    $samp =~ s/.*A[0-9]+.samp([0-9]+).+/$1/; #gets the samp#
	    $SentPair =~ s/.*A[0-9]+.samp[0-9]+\.SentPair([0-9]+).*/$1/; #gets the SentPair#
	    $temp3 =~ s/^(.*)A[0-9]+.+/$1/; #this is the beginning part of the directory
	    $temp4 =~ s/^.*SentPair[0-9]+(.*)/$1/;  #checks for anything after the SentPair (.open etc)

	    #check for extreme cases
	    if($SentPair == 0){
		#if samp# is at the lower limit
		if($samp == 1){
		    #if annotator is at lower limit
		    if($A == 1){
			#wrap around if this is the first file
			$A = $an;
		    }
		    else{
			$A--;
		    }
		    #wrap around
		    $samp = $sam;
		    $SentPair = $v-1;
		    
		    #set $sent to the new file
		    $blinkfile = $sent = $temp3."A".$A."/samp".$samp.".SentPair".$SentPair.$temp4;
		
		    #Check if there is an annotator for this file
		    if(!open(TEST, $sent)){
			$info = "Error opening $sent, No annotator for this file";
			$entry1_w->bell();
			return(-1);
		    }
		    close (TEST);

		    #load the previous file if possible
		    &openb;
		    $info = $sent." Loaded";
		    return;
		}

		#else not a total extreme case, just adjust for SentPair extreme
		else{
		    #decrement samp#, wrap SentPair around
		    $samp--;
		    $SentPair = $v-1;
		    
		    #set $sent to the new file
		    $blinkfile = $sent = $temp3."A".$A."/samp".$samp.".SentPair".$SentPair.$temp4;
		
		    #Check if there is an annotator for this file
		    if(!open(TEST, $sent)){
			$info = "Error opening $sent, No annotator for this file";
			$entry1_w->bell();
			return(-1);
		    }
		    close (TEST);

		    #load previous file if possible
		    &openb;
		    $info = $sent." Loaded";
		    return;
		}
	    }
	    
	    #else no extreme at all, just decrement SentPair and load
	    elsif($SentPair != 0){
		$SentPair--;
	    
		#set $sent to the new file
		$blinkfile = $sent = $temp3."A".$A."/samp".$samp.".SentPair".$SentPair.$temp4;
		
		#Check if there is an annotator for this file
		if(!open(TEST, $sent)){
		    $info = "Error opening $sent, No annotator for this file";
		    $entry1_w->bell();
		    return(-1);
		}
		close (TEST);

		#load the previous file if possible
		&openb;
		$info = $sent." Loaded";
		return;
	    }
	}
    }
}
#-----------------------------------------------------------------------------
#next end


#This function will display the sentences in a text widget popup
sub show_sentences{

#make the toplevel widget with the text widget inside it
$t10 = $mw->Toplevel();

#withdraw for different pop-up method
$t10->withdraw();
$t10->title("Verse Display");
$sentences = $t10->Scrolled("Text")->pack();

#insert the sentences into the text widget
$sentences->insert("end",$sentence1."\n");
$sentences->insert("end","=" x 80);
$sentences->insert("end","\n\n".$sentence2."\n\n");

#disable the text widget for read-only status
$sentences->configure(-state,'disabled');

#make a close button, and insert it into the text widget
my $close = $t10->Button(-text,"Close",-background,"blue",-foreground,"white",-command,sub{$t10->withdraw});
$sentences->windowCreate('end',-window,$close);

#makes toplevel pop-up
$t10->Popup;
$t10->focus();

return;
}
#-----------------------------------------------------------------------------
#show_sentences end


__END__



=head1 NAME

alpaco.pl - Aligner for Paralell corpora

=head1 SYNOPSIS

perl alpaco.pl

=head1 DESCRIPTION

Aligner for Parallel Corpora (Alpaco) is a program that is designed to 
align bilingual parallel texts.  If two files are known to be translations 
of each other, Alpaco can be used to manually align them and save the 
alignments for future reference.  

Alpaco can take the following as input:  raw text files, Blinker data 
(explained in section 3 of the README), and previously aligned text files 
(Alpaco format).  It also has the ability to read in raw text files line-by-
line for easier use with large text files.  This gets a bit more complicated 
with the naming scheme, which is explained in the README. 

=head1 AUTHOR

Alpaco was written by Brian Rassier <rass0028@d.umn.edu> as a research 
project for Dr. Ted Pedersen <tpederse@d.umn.edu>


=head1 SEE ALSO

For information about naming standards, file types and general Alpaco usage
please see the README that was distributed with the Alpaco package.

=cut

    
