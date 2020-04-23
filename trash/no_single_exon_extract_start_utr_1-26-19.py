def no_one_extract_start_utr(bed_list_raw, tmp_dir):
    
    output_write = open(tmp_dir+'no_one_start_utr.bed', 'w')
    
    for fields in bed_list_raw:
        if '_' not in fields[0]:
            strand = fields[5]
            tx_start = fields[1]
            tx_end = fields[2]  
            abs_exon_starts = [int(tx_start)+int(i) for i in fields[11].strip(',').split(',')]
            exon_sizes = [int(i) for i in fields[10].strip(',').split(',')]         
            
            if strand == '+':
                tx_end = str(int(tx_start) + int(exon_sizes[0]))
                exon_sizes = str(exon_sizes[0])
                rel_exon_starts = (',').join([str(int(i)-int(tx_start)) for i in abs_exon_starts])[0]
            
            elif strand == '-':
                tx_start = str(int(tx_end) - int(exon_sizes[-1]))
                exon_sizes = str(exon_sizes[-1])
                rel_exon_starts = (',').join([str(int(i)-int(tx_start)) for i in abs_exon_starts])[-1]
                
            else:
                continue
            
            if fields[9] != '1':
                write_line = [fields[0], tx_start, tx_end, fields[3], '0', strand, fields[6], fields[7], '255, 0, 0', '1', exon_sizes, rel_exon_starts]
                output_write.writelines('\t'.join(write_line) + '\n')
     
    output_write.close()
    