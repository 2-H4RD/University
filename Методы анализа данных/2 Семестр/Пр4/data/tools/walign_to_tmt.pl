#!/usr/bin/perl

# Conversion from the word alignment file (WA format) into the TMT format. 

# Written by David Marecek

use strict;
use warnings;

binmode STDIN, ":encoding(utf-8)";
binmode STDOUT, ":encoding(utf-8)";

sub cs_entity_substitution($) {
  my $text = shift;
  $text =~ s/\&/\&amp;/g;
  $text =~ s/\&percnt;/\%/g;
  $text =~ s/\&dollar;/\$/g;
  return $text;
}

sub en_entity_substitution($) {
  my $text = shift;
  $text =~ s/\&/\&amp;/g;
  $text =~ s/\&dollar;/\$/g;
  $text =~ s/\&lsqb;/-LSB-/g;
  $text =~ s/\&rsqb;/-RSB-/g;
  $text =~ s/\(/-LRB-/g;
  $text =~ s/\)/-RRB-/g;
  $text =~ s/\[/-LSB-/g;
  $text =~ s/\]/-RSB-/g;
  $text =~ s/\{/-LCB-/g;
  $text =~ s/\}/-RCB-/g;
  return $text;
}

my @en_tokens;
my @cs_tokens;
my $current_id;
my @sure;
my @possible;
my @phrasal;

print "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n\n";
print "<tmt_document xmlns=\"http://ufal.mff.cuni.cz/pdt/pml/\">\n";
print " <head>\n";
print "  <schema href=\"tmt_schema.xml\" />\n";
print " </head>\n";
print " <meta />\n";
print " <bundles>\n";
while (<>) {
  chomp;
  if ($_ =~ /^<s id=\"(.*)\">/) {
    $current_id = $1;
    print "  <LM id=\"$current_id\">\n";
  }
  elsif ($_ =~ /<english>(.*)<\/english>/) {
    my $en_sent = en_entity_substitution($1);
    @en_tokens = split(/ /, $en_sent);
    print "   <english_source_sentence>$en_sent</english_source_sentence>\n";
  }
  elsif ($_ =~ /<czech>(.*)<\/czech>/) {
    my $cs_sent = cs_entity_substitution($1);
    @cs_tokens = split(/ /, $cs_sent);
    print "   <czech_source_sentence>$cs_sent</czech_source_sentence>\n";
  }
  elsif ($_ =~ /<sure>(.*)<\/sure>/) {
    foreach my $p (split (/ /, $1)) {
      my ($e, $c) = split(/-/, $p);
      $sure[$c-1] .= "SEnglishM-${current_id}w$e ";
    }
  }      
  elsif ($_ =~ /<possible>(.*)<\/possible>/) {
    foreach my $p (split (/ /, $1)) {
      my ($e, $c) = split(/-/, $p);
      $possible[$c-1] .= "SEnglishM-${current_id}w$e ";
    }
  }
  elsif ($_ =~ /<phrasal>(.*)<\/phrasal>/) {
    foreach my $p (split (/ /, $1)) {
      my ($e, $c) = split(/-/, $p);
      $phrasal[$c-1] .= "SEnglishM-${current_id}w$e ";
    }
  }
  elsif ($_ =~ /<\/s>/) {
    print "   <trees>\n";
    print "    <SCzechM>\n";
    print "     <children>\n";
    for (my $t = 0; $t < @cs_tokens; $t++) {
      print "      <LM id=\"SCzechM-$current_id-w".($t+1)."\">\n";
      print "       <form>$cs_tokens[$t]</form>\n";
      if ($sure[$t] or $possible[$t]) {
        print "       <walign>\n";
        if ($sure[$t]) {
          print "        <sure.rf>\n";
          my @wa = split(/\ /, $sure[$t]);
          foreach my $rf (@wa) {
            print "         <LM>$rf</LM>\n";
          }
          print "        </sure.rf>\n";
        }  
        if ($possible[$t]) {
          print "        <possible.rf>\n";
          my @wa = split(/\ /, $possible[$t]);
          foreach my $rf (@wa) {
            print "         <LM>$rf</LM>\n";
          }
          print "        </possible.rf>\n";
        }
        if ($phrasal[$t]) {
          print "        <phrasal.rf>\n";
          my @wa = split(/\ /, $phrasal[$t]);
          foreach my $rf (@wa) {
            print "         <LM>$rf</LM>\n";
          }
          print "        </phrasal.rf>\n";
        }
        print "       </walign>\n";
      }
      print "      </LM>\n";
    }
    print "     </children>\n";
    print "    </SCzechM>\n";
    print "    <SEnglishM>\n";
    print "     <children>\n";
    for (my $t = 0; $t < @en_tokens; $t++) {
      print "      <LM id=\"SEnglishM-${current_id}w".($t+1)."\">\n";
      print "       <form>$en_tokens[$t]</form>\n";
      print "      </LM>\n";
    }
    print "     </children>\n";
    print "    </SEnglishM>\n";
    print "   </trees>\n";
    print "  </LM>\n";
    @sure = ();
    @possible = ();
  }
}
print " </bundles>\n";
print "</tmt_document>\n";

