#!/usr/bin/perl

# Merge two WA files aligned by different annotators into one file.
# Requires two arguments (filenames).
# Merged WA is written on STDOUT. 

# Written by David Marecek

use strict;
use warnings;

binmode STDOUT, ":encoding(utf-8)";

my $actual_id = "";
my %sure1;
my %possible1;
my %phrasal1;

open(WA1, "<:encoding(utf-8)", $ARGV[0]) or die;
while (<WA1>) {
  chomp;
  if ($_ =~ /^<s id=\"(.*)\".*$/) {
    $actual_id = $1;
  }
  elsif ($_ =~ /<sure>(.*)<\/sure>/) {
    $sure1{$actual_id} = $1;
  }
  elsif ($_ =~ /<possible>(.*)<\/possible>/) {
    $possible1{$actual_id} = $1;
  }
  elsif ($_ =~ /<phrasal>(.*)<\/phrasal>/) {
    $phrasal1{$actual_id} = $1;
  }
}
close WA1;

my $sure2;
my $possible2;
my $phrasal2;
open(WA2, "<:encoding(utf-8)", $ARGV[1]) or die;
print "<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n";
print "<sentences>\n";
while (<WA2>) {
  chomp;
  if ($_ =~ /^<s id=\"(.*)\".*$/) {
    $actual_id = $1;
    print "$_\n";
  }
  elsif ($_ =~ /(<english>.*<\/english>)/) {
    print "  $1\n";
  }
  elsif ($_ =~ /(<czech>.*<\/czech>)/) {
    print "  $1\n";
  }
  elsif ($_ =~ /<sure>(.*)<\/sure>/) {
    $sure2 = $1;
  }
  elsif ($_ =~ /<possible>(.*)<\/possible>/) {
    $possible2 = $1;
  }
  elsif ($_ =~ /<phrasal>(.*)<\/phrasal>/) {
    $phrasal2 = $1;
  }
  elsif ($_ =~ /<\/s>/) {
    my %s1;
    my %s2;
    my %p;
    my $sure = "";
    my $possible = "";
    foreach my $a (split(/ /, $possible1{$actual_id})) {
      $p{$a}++;
    }
    foreach my $a (split(/ /, $phrasal1{$actual_id})) {
      $p{$a}++;
    }
    foreach my $a (split(/ /, $sure1{$actual_id})) {
      $s1{$a} = 1;
      $p{$a}++;
    }
    foreach my $a (split(/ /, $possible2)) {
      $p{$a}++;
    }
    foreach my $a (split(/ /, $phrasal2)) {
      $p{$a}++;
    }
    foreach my $a (split(/ /, $sure2)) {
      $s2{$a} = 1;
      $p{$a}++;
    }
    foreach my $a (sort keys %p) {
      my @num = split(/-/, $a);
      next if $num[0] eq "0" or $num[1] eq "0";
      if ($p{$a} > 1 && ($s1{$a} or $s2{$a})) {
        $sure .= $a." ";
      }
      else {
        $possible .= $a." ";
      }
    }
    $sure =~ s/\ $//;
    $possible =~ s/\ $//;
    print "  <sure>$sure</sure>\n";
    print "  <possible>$possible</possible>\n";
    print "</s>\n";
  }
}
print "</sentences>\n";
close WA2;


    

      




