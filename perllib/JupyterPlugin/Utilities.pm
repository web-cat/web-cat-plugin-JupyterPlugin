#========================================================================
package JupyterPlugin::Utilities;
#========================================================================
use warnings;
use strict;
use JSON;
use MIME::Base64;

use vars qw(@ISA @EXPORT);
use Exporter qw(import);
@ISA = qw(Exporter);
@EXPORT = qw(
  nl_expand
  load_notebook
  remove_embedded_solutions
  extract_solution
  extract_starter
  extract_images
  extract_imports
  extract_tests
  );


#========================================================================
sub nl_expand {
    my $text = shift;
    $text =~ s/\n/<\/br>/gi;
    return $text;
}


#========================================================================
sub load_notebook {
    my $filename = shift;

    open F, $filename or die "Can't read $filename: $!";
    local $/;  # enable slurp mode, locally.
    my $file = <F>;
    close F;
    return JSON->new->decode($file);
}


#========================================================================
sub remove_embedded_solutions {
    my $lines = shift;
    my $result = [];
    my $in_solution = 0;
    for my $line (@{$lines})
    {
        if ($in_solution)
        {
            if ($line =~ /^\#\#\#\s+end\s+solution\b/io)
            {
                $in_solution = 0;
            }
        }
        else
        {
            if ($line =~ /^\#\#\#\s+begin\s+solution\b/io)
            {
                $in_solution = 1;
                push(@{$result}, "# Insert your work here\n", "\n", "\n");
            }
            else
            {
                push(@{$result}, $line);
            }
        }
    }
    return $result;
}


#========================================================================
# generate student code
sub extract_solution {
    my $result = [];
    my $contents = shift;

    for my $cell (@{$contents->{'cells'}})
    {
        if ($cell->{'cell_type'} eq 'code')
        {
            my $lines = $cell->{'source'};
            for my $line (@{$lines})
            {
                push(@{$result}, $line);
            }
            push(@{$result}, pop(@{$result}) . "\n");
        }
    }
    return $result;
}


#========================================================================
# generate student code
sub extract_starter {
    my $nb = {};
    my $contents = shift;

    while (my ($k, $v) = each %{$contents})
    {
        if ($k eq 'cells')
        {
            my $result = [];
            for my $cell (@{$v})
            {
                if ($cell->{'cell_type'} eq 'code')
                {
                    if (!$cell->{'metadata'}->{'nbgrader'}->{'grade'})
                    {
                        my $newcell = {};
                        while (my ($kk, $vv) = each %{$cell})
                        {
                            if ($kk eq 'source')
                            {
                                $vv = remove_embedded_solutions($vv);
                            }
                            elsif ($kk eq 'outputs')
                            {
                                $vv = [];
                            }
                            elsif ($kk eq 'execution_count')
                            {
                                $vv = JSON::null;
                            }
                            $newcell->{$kk} = $vv;
                        }
                        push(@{$result}, $newcell);
                    }
                }
                else
                {
                    push(@{$result}, $cell);
                }
            }
            $nb->{$k} = $result;
        }
        else
        {
            $nb->{$k} = $v;
        }
    }
    return $nb;
}


#========================================================================
# extract embedded images
sub extract_images {
    my $contents = shift;
    my $cfg = shift;
    my $pngCounter = 0;

    for my $cell (@{$contents->{'cells'}})
    {
        if ($cell->{'cell_type'} eq 'code'
            && $cell->{'outputs'})
        {
            for my $output (@{$cell->{'outputs'}})
            {
                if ($output->{'output_type'} eq 'display_data')
                {
                    my $pngContent = $output->{'data'}->{'image/png'};
                    if ($pngContent)
                    {
                        $pngCounter++;
                        my $filename = $cfg->getProperty('resultDir')
                            . "/public/$pngCounter.png";
                        open(IMG, "> :raw :bytes", $filename)
                            || die "Cannot open '$filename': $!";
                        print IMG decode_base64($pngContent);
                        close(IMG);
                    }
                }
            }
        }        
    }
    return $pngCounter;
}


#========================================================================
# extract import lines from non-graded cells
sub extract_imports {
    my $result = '';
    my $contents = shift;
    my $test_counter = 0;

    for my $cell (@{$contents->{'cells'}})
    {
        if ($cell->{'cell_type'} eq 'code'
            && !$cell->{'metadata'}->{'nbgrader'}->{'grade'})
        {
            my $lines = $cell->{'source'};
            for my $line (@{$lines})
            {
                if ($line =~ /^import\s/o)
                {
                    $result .= $line;
                }
            }
        }
    }
    return $result;
}


#========================================================================
# extract instructor test case code
sub extract_tests {
    my $result = [];
    my $contents = shift;
    my $test_counter = 0;

    for my $cell (@{$contents->{'cells'}})
    {
        if ($cell->{'cell_type'} eq 'code'
            && $cell->{'metadata'}->{'nbgrader'}->{'grade'})
        {
            $test_counter++;
            my $id = $cell->{'metadata'}->{'nbgrader'}->{'grade_id'};
            my $points = $cell->{'metadata'}->{'nbgrader'}->{'points'};
            
            push(@{$result}, "  # -----------------------------------------"
                . "--------------------\n");
            push(@{$result}, 
                "  def test_$test_counter(self):\n");
            push(@{$result}, "    \"\"\"$id\"\"\"\n");

            my $lines = $cell->{'source'};
            my %names = ();
            for my $line (@{$lines})
            {
                my @matches = ($line =~ m/\b(Answer[0-9]+)\b/g);
                for my $match (@matches)
                {
                    $names{$match} = $match;
                }
            }
            for my $name (keys %names)
            {
                push(@{$result}, "    $name = self.lookup('$name')\n");
            }
            for my $line (@{$lines})
            {
                push(@{$result}, '    ' . $line);
            }
            push(@{$result}, pop(@{$result}) . "\n");

            push(@{$result}, 
                "  test_$test_counter.points = $points\n");
            push(@{$result}, 
                "  test_$test_counter.nbgrader_id = \"$id\"\n");
        }
    }
    return $result;
}


# ---------------------------------------------------------------------------
1;
# ---------------------------------------------------------------------------
