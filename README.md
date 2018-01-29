# APARDIUML
Alternative PolyAdenylation from RNA sequencing and DNA sequence Information Using Machine Learning
#!/bin/bash python3

import sys
import getopt
import os
import gzip
import datetime
import re
import shutil

def extraction_main(argv):
     
    org = ''
    gene_bed_file = ''
    gene_symbol_file = ''
    Cufflinks_or_StringTie_gtf_file = ''
    fasta_file = ''
    chrom_sizes_file = ''
    sorted_bam_file = ''
    stranded_data = 'no'
        
    curr_time = datetime.datetime.now()
    temp_dir = os.getcwd()+'/'+curr_time.strftime('%c')+'_tmp/'
    temp_dir = temp_dir.replace(' ', '_')
    temp_dir = temp_dir.replace(':', '_')
    os.makedirs(temp_dir)
    
    try:
        opts, args = getopt.getopt(argv, 'ho:b:s:c:g:f:m:d', ['help', 'organism=', 'bed=', 'symbol=', 'chroms=', 'gtf=', 'fasta=', 'bam=', 'stranded='])
    except getopt.GetoptError:
        print('python extract_annot_and_seq.py -o <organism> -b <gene_bed_file> -s <gene_symbol_file> -c <chromosome_sizes_file> -g <gtf_file> -f <fasta_file>\nType -h (or --help) for usage')
        shutil.rmtree(temp_dir, ignore_errors = True)
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            usage()
            shutil.rmtree(temp_dir, ignore_errors = True)
            sys.exit()
        elif opt in ('-o', '--organism'):
            org = arg
        elif opt in ('-b', '--bed'):
            gene_bed_file = arg
        elif opt in ('-s', '--symbol'):
            gene_symbol_file = arg
        elif opt in ('-c', '--chroms'):
            chrom_sizes_file = arg
        elif opt in ('-g', '--gtf'):
            Cufflinks_or_StringTie_gtf_file = arg
        elif opt in ('-f', '--fasta'):
            fasta_file = arg
        elif opt in ('-m', '--bam'):
            sorted_bam_file = arg
        elif opt in ('-d', '--stranded'):  
            stranded_data = 'yes'
            
    if org != '' and sorted_bam_file != '' and gene_bed_file == '' and gene_symbol_file == '' and chrom_sizes_file == '' and Cufflinks_or_StringTie_gtf_file == '' and fasta_file == '':
        try:
            os.system('rsync -a -q %s %s' % ('rsync://hgdownload.cse.ucsc.edu/goldenPath/'+org+'/database/chromInfo.txt.gz', temp_dir))
            os.system('rsync -a -q %s %s' % ('rsync://hgdownload.cse.ucsc.edu/goldenPath/'+org+'/database/refGene.txt.gz', temp_dir))
            chrom_sizes = get_chrom_sizes(temp_dir+'chromInfo.txt.gz')
            annot_from_download(temp_dir, chrom_sizes)
            os.system('rsync -a -q %s %s' % ('rsync://hgdownload.cse.ucsc.edu/goldenPath/'+org+'/bigZips/'+org+'.fa.gz', temp_dir))
            print('fasta file download completed %s' % (time_now()))
            fasta_file = temp_dir+org+'.fa.gz'
        except:
            shutil.rmtree(temp_dir, ignore_errors = True)
            print('Unexpected error encountered')
            sys.exit(2)
    elif gene_bed_file != '' and gene_symbol_file != '' and chrom_sizes_file != '' and fasta_file != '' and sorted_bam_file != '' and org == '' and Cufflinks_or_StringTie_gtf_file == '':
        try:
            chrom_sizes = get_chrom_sizes(chrom_sizes_file)
            annot_from_bed(gene_bed_file, temp_dir, chrom_sizes, gene_symbol_file)
        except:
            shutil.rmtree(temp_dir, ignore_errors = True)
            print('Unexpected error encountered')
            sys.exit(2)
    elif Cufflinks_or_StringTie_gtf_file != '' and chrom_sizes_file != '' and fasta_file != '' and sorted_bam_file != '' and gene_bed_file == '' and gene_symbol_file == '' and org == '':
        try:
            gtf_to_bed(Cufflinks_or_StringTie_gtf_file, temp_dir)
            chrom_sizes = get_chrom_sizes(chrom_sizes_file)
            annot_from_bed(temp_dir+'bed_from_gtf.bed', temp_dir, chrom_sizes)
        except:
            shutil.rmtree(temp_dir, ignore_errors = True)
            print('Unexpected error encountered')
            sys.exit(2)
    else:
        print('python3 apardi.py -o <organism> -b <gene_bed_file> -s <gene_symbol_file> -c <chromosome_sizes_file> -g <gtf_file> -f <fasta_file> -m <sorted_bam_file> -d <stranded>')
        shutil.rmtree(temp_dir, ignore_errors = True)
        print('Incorrect combinations of arguments\nType -h (or --help) for usage')
        sys.exit()
        
    sequence_from_fasta(fasta_file, temp_dir)
    print('Transcript block sequences extracted %s' % (time_now())) 
    bam_to_bedgraph(sorted_bam_file, temp_dir, stranded_data)
    print('RNA sequencing data extracted and converted to bedgraph format %s' % (time_now()))
 
       
def usage():
    usage = """
    -h --help                 Prints this
    
    -o --organism             The name of the desired organism located on UCSC's FTP server (ftp://hgdownload.cse.ucsc.edu/goldenPath/)
                              The specified organism name must have associated .fa.gz, refGene.txt.gz, and chromInfo.txt.gz files located in its bigZips, database, and database directories, respectively
                              Example usage: -o rn6
                              If using the -o argument, ONLY use the -m argument (and optionally the -d argument) below
                              
    -b --bed                  Path to the gene bed file
                              If using the -b argument, you must also use the -s, -c, -f, and -m arguments
    
    -s --symbol               Path to the gene symbol file
                              If using the -s argument, you must also use the -b, -c, -f, and -m arguments
                              
    -c --chroms               Path to the chromosome sizes file
                              If using the -c argument, you must also use the -b, -s, -f, and -m arguments
    
    -g --gtf                  Path to the gtf file outputted by Cufflinks or StringTie
                              If using the -g argument, you must also use the -c, -f, and -m arguments
    
    -f --fasta                Path to the fasta sequence file
                              If uing the -f argument, you must also use either
                              1. The -b AND -s AND -c AND -m arguments
                              OR
                              2. The -c AND -g AND -m arguments
                              
    -m --bam                  Path to the sorted bam file of RNA sequencing data
    
    -d --stranded             Argument to indicate if the RNA sequencing data are stranded
                              
                              The gtf file should be in the format outputted by Cufflinks or StringTie
                                  These algorithms can be performed on a sorted bam file generated from the RNA sequencing data (see below for how to produce a sorted bam file) to yield an experiment-specific gtf file (recommended)
                              The gene bed, symbol, and chromosome sizes files can be generated from UCSC
                              The chromosome sizes text file should have a line for each chromsome with 2 tab separated fields for each line:
                                  1st field = chromosome, either with or without a leading 'chr'
                                  2nd field = chromosome size
                                  Note: The chromosome sizes file can have comment lines and empty lines
                              The fasta and chromosome sizes file can be .gz compressed
                              The bam file should be sorted 
                                  hisat2/bowtie2 can be used to map RNA sequencing reads
                                  samtools view with the -b argument (i.e. bam file output) can then be used on these data to generate a bam file
                                  Finally, samtools sort can be used to sort the resulting bam file
                              See supporting documentation for more information
    """
    print(usage)


def time_now():
    
    curr_time = datetime.datetime.now()
    return curr_time.strftime('%c')   


def annot_from_bed(user_bed_path, tmp_dir, chrom_sizes_dict, user_symbol_path = None):
    
    bed_file = user_bed_path
    symbol_file = user_symbol_path
    symbol_dict = {}
    line_num = 0
    output_write = open(tmp_dir+'modified_annot.bed', 'w')
    
    if symbol_file != None:
        with open(symbol_file, 'r') as f:
            for line in f:
                if line_num > 0:
                    fields = line.strip('\n').strip('\r').split('\t')
                    symbol_dict[fields[0]] = fields[1]
                line_num += 1
            
    with open(bed_file, 'r') as f:
        for line in f:
            fields = line.strip('\n').split('\t')
            if '_' not in fields[0]:
                if fields[3] not in symbol_dict:
                    fields.append('NA')
                else:
                    fields.append(symbol_dict[fields[3]])
                strand = fields[5]
                tx_start = fields[1]
                tx_end = fields[2]  
                abs_exon_starts = [int(tx_start)+int(i) for i in fields[11].strip(',').split(',')]
                exon_sizes = [int(i) for i in fields[10].strip(',').split(',')]
            
                if strand == '+' and int(fields[10].strip(',').split(',')[-1]) < 10000:
                    extended_UTR = str(int(tx_end) + (10000 - int(fields[10].strip(',').split(',')[-1]))) 
                    if fields[0] in chrom_sizes_dict:
                        total_chrom_length = chrom_sizes_dict[fields[0]][0]
                        if int(total_chrom_length) < int(extended_UTR):
                            extended_UTR = total_chrom_length
                    tx_end = extended_UTR
                    exon_sizes[-1] = int(tx_end)-abs_exon_starts[-1]
                            
                elif strand == '-' and int(fields[10].strip(',').split(',')[0]) < 10000:
                    extended_UTR = str(int(tx_start) - (10000 - int(fields[10].strip(',').split(',')[0])))
                    if int(extended_UTR) < 0:
                        extended_UTR = '0'
                    tx_start = extended_UTR
                    abs_exon_starts[0] = int(extended_UTR)
                    exon_sizes[0] = int(fields[1])-int(tx_start)+exon_sizes[0]
                    
                rel_exon_starts = (',').join([str(int(i)-int(tx_start)) for i in abs_exon_starts])
                exon_sizes = (',').join(str(i) for i in exon_sizes)
                if symbol_file != None:
                    new_id = [fields[3], fields[12], fields[0], fields[1], fields[2], strand]
                    new_bed_id = '|'.join(new_id)
                else:
                    new_bed_id = fields[3]
                write_line = [fields[0], tx_start, tx_end, new_bed_id, '0', strand, fields[6], fields[7], '255, 0, 0', fields[9], exon_sizes, rel_exon_starts]
                output_write.writelines('\t'.join(write_line) + '\n')
            
    output_write.close()
    print('Transcript annotations completed %s' % (time_now()))


def annot_from_download(refGene_path, chrom_sizes_dict):
    
    file = refGene_path+'refGene.txt.gz'
    output_write = open(refGene_path+'modified_annot.bed', 'w')
    
    with gzip.open(file, 'rt') as f:
        for line in f:
            fields = line.strip('\n').split('\t')
            if '_' not in fields[2]:
                strand = fields[3]
                tx_start = fields[4]
                tx_end = fields[5]                   
            
                if strand == '+':
                    UTR_start = fields[9].strip(',').split(',')[-1]
                    UTR_length = abs(int(UTR_start) - int(tx_end))
                    if UTR_length < 10000:
                        extended_UTR = str(int(tx_end) + (10000 - UTR_length))
                        if fields[2] in chrom_sizes_dict:
                            total_chrom_length = chrom_sizes_dict[fields[2]][0]
                            if int(total_chrom_length) < int(extended_UTR):
                                extended_UTR = total_chrom_length
                        extended_exons = fields[10].strip(',').split(',')
                        extended_exons[-1] = extended_UTR
                        fields[10] = (',').join(extended_exons)
                        tx_end = extended_UTR
                            
                elif strand == '-':
                    UTR_start = fields[10].strip(',').split(',')[0]
                    UTR_length = abs(int(UTR_start) - int(tx_start))
                    if UTR_length < 10000:
                        extended_UTR = str(int(tx_start) - (10000 - UTR_length))
                        if int(extended_UTR) < 0:
                            extended_UTR = '0'
                        extended_exons = fields[9].strip(',').split(',')
                        extended_exons[0] = extended_UTR
                        fields[9] = (',').join(extended_exons)
                        tx_start = extended_UTR
                            
                rel_exon_starts = (',').join([str(int(i)-int(tx_start)) for i in fields[9].strip(',').split(',')])
                exon_sizes = (',').join([str(int(a)-int(b)) for a, b in zip(fields[10].strip(',').split(','), fields[9].strip(',').split(','))])
                num_exons = str(len(fields[10].strip(',').split(',')))
                new_id = [fields[1], fields[12], fields[2], fields[4], fields[5], strand]
                new_bed_id = '|'.join(new_id)
                write_line = [fields[2], tx_start, tx_end, new_bed_id, '0', strand, fields[6], fields[7], '255, 0, 0', num_exons, exon_sizes, rel_exon_starts]
                output_write.writelines('\t'.join(write_line) + '\n')


    output_write.close()
    print('Transcript annotations completed %s' % (time_now()))
    

def gtf_to_bed(gtf_file, tmp_dir):
    
    
    def bed_line(estart, eend, field, nline, exon_coverage, trans_coverage):
        
        allids = {}
        estp = estart[0] - 1
        eedp = eend[-1]
        geneid = re.findall(r'gene_name \"([\w\.]+)\"', field[8])
        if len(geneid) == 0:
            geneid = re.findall(r'ref_gene_name \"([\w\.]+)\"', field[8])
        if len(geneid) == 0:
            geneid = re.findall(r'gene_id \"([\w\.]+)\"', field[8])   
        if len(geneid) == 0:
            geneid = 'NA'
        else:
            geneid = geneid[0]
        transid = re.findall(r'reference_id \"([\w\.]+)\"', field[8])
        if len(transid) == 0:
            transid = re.findall(r'transcript_id \"([\w\.]+)\"', field[8])
        if len(transid) == 0:
            transid = 'Trans_' + str(nline)
        else:
            transid = transid[0]
        if transid in allids.keys():
            transid2 = transid + '_DUP' + str(allids[transid])
            allids[transid] = allids[transid] + 1
            transid = transid2
        else:
            allids[transid] = 1
        if not field[0].startswith('chr'):
            field[0] = 'chr' + field[0]
        line = [field[0], str(estp), str(eedp), '|'.join([transid, geneid, field[0], str(estp), str(eedp), field[6]]), ','.join(exon_coverage), field[6], str(estp), str(eedp), str(trans_coverage), str(len(estart))]
        seglen = [eend[i] - estart[i] + 1 for i in range(len(estart))]
        segstart = [estart[i] - estart[0] for i in range(len(estart))]
        strl = str(seglen[0])
        for i in range(1, len(seglen)):
            strl += ',' + str(seglen[i])
        strs = str(segstart[0])
        for i in range(1, len(segstart)):
            strs +=',' + str(segstart[i])
        line.extend([strl, strs])
        
        return line
    
    
    extracted_bed_line = open(tmp_dir+'bed_from_gtf.bed', 'w')
    
    estart = []
    eend = []
    exon_coverage = []
    trans_coverage = []
    nline = 0
    prevfield = []
    prevtransid = ''
    with open(gtf_file, 'r') as f:
        for lines in f:
            if lines.strip().split('\t')[0] == '\n' or lines[0] == '#':
                pass
            else:
                field = lines.strip().split('\t')
                field[8:] = [(' ').join(field[8:])]
                nline = nline + 1
                if field[1] not in ['Cufflinks', 'StringTie']:
                    print('Warning: The GTF file may not have been produced by Cufflinks or StringTie and therefore may give erroneous results')
                    pass
                if field[2] != 'exon' and field[2] != 'transcript':
                    continue
                transid = re.findall(r'transcript_id \"([\w\.]+)\"', field[8])
                if len(transid) > 0:
                    transid = transid[0]
                else:
                    transid = ''
                if field[2] == 'transcript' or (prevtransid != '' and transid != '' and transid != prevtransid):
                    if len(estart) != 0:
                        extracted_bed_line.writelines('\t'.join(bed_line(estart, eend, prevfield, nline, exon_coverage, trans_coverage)) + '\n')
                    estart = []
                    eend = []
                    exon_coverage = []
                    trans_coverage = []
                prevfield = field
                prevtransid = transid
                if field[2] == 'exon':
                    est = int(field[3])
                    eed = int(field[4])
                    exon_cov = re.findall(r'cov \"([\d\.]+)\"', field[8])
                    if len(exon_cov) == 0:
                        exon_cov = ['NA']
                    estart += [est]
                    eend += [eed]
                    exon_coverage.extend(exon_cov)
                if field[2] == 'transcript':
                    trans_cov = re.findall(r'cov \"([\d\.]+)\"', field[8])
                if len(trans_cov) == 0:
                    trans_coverage = '255,0,0'
                else:
                    trans_coverage = trans_cov[0]
        if len(estart) != 0:
            extracted_bed_line.writelines('\t'.join(bed_line(estart, eend, prevfield, nline, exon_coverage, trans_coverage)) + '\n')
                
    extracted_bed_line.close()


def get_chrom_sizes(chrom_file):
    
    chrom_sizes_dict = {}
    
    if chrom_file.endswith('.gz'):
        os.system('gunzip -f %s' % (chrom_file))
        chrom_file = chrom_file[:-3]
        
    with open(chrom_file, 'r') as f:
        for line in f:
            fields = line.strip('\n').split('\t')
            if line.strip().split('\t')[0] == '\n' or line[0] == '#':
                pass
            elif '_' not in fields[0]:
                chrom = fields[0]
                chrom_size = fields[1]
                if not chrom.startswith('chr'):
                    chrom = 'chr' + chrom
            chrom_sizes_dict[chrom] = [chrom_size]
            
    return chrom_sizes_dict


def sequence_from_fasta(local_fasta_file, tmp_dir):
    
    if local_fasta_file.endswith('.gz'):
        os.system('gunzip -f %s' % (local_fasta_file))
        local_fasta_file = local_fasta_file[:-3]
    
    os.system('bedtools getfasta -fi %s -bed %s modified_annot.bed -name -bedOut -s > %smodified_bed_with_sequence.bed' % (local_fasta_file, tmp_dir, tmp_dir))


def bam_to_bedgraph(user_bam_path, tmp_dir, strdat):
    
    if strdat == 'no':
        os.system('bedtools genomecov -bg -ibam %s > %s' % (user_bam_path, tmp_dir+'coverage.bedgraph'))
        
    elif strdat == 'yes':
        os.system('bedtools genomecov -bg -strand + -ibam %s > %s' % (user_bam_path, tmp_dir+'coverage_plus_strand.bedgraph'))
        os.system('bedtools genomecov -bg -strand - -ibam %s > %s' % (user_bam_path, tmp_dir+'coverage_minus_strand.bedgraph'))
        os.system('bedtools unionbedg -i %s %s > %s' % (tmp_dir+'coverage_plus_strand.bedgraph', tmp_dir+'coverage_minus_strand.bedgraph', tmp_dir+'coverage.bedgraph'))
        os.remove(tmp_dir+'coverage_plus_strand.bedgraph')
        os.remove(tmp_dir+'coverage_minus_strand.bedgraph')


if __name__ == '__main__':
    extraction_main(sys.argv[1:])
