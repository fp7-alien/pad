
ROFL_DIR = "/home/geysers-wp5"

def read_template(filename):
    return file(filename, 'r').read()
    
def generate_file(filename, content):
    f = file(filename, 'w')
    f.write(content)
    f.close()
    
def generate_openflow_pipeline_action_h(fields):
    skeleton = read_template("of1x_action.h.template")
    
    for field in fields:
        field['header_upper'] = field['header'].upper()
        if 'field' in field:
            field['field_upper'] = field['field'].upper()
        field['action_upper'] = field['action'].upper()
        
        if int(field['length']) % 8 !=0:
            field['masking'] = '%s_BITS' % field['length']
        else:
            field['masking'] = '%d_BYTE' % (int(field['length'])/8,)
        
    code1 = ""
    for field in fields:
        if 'field' not in field:
            code1 += "\tOF1X_AT_%(action_upper)s_%(header_upper)s,\n" % field
        else:
            code1 += "\tOF1X_AT_%(action_upper)s_FIELD_%(header_upper)s_%(field_upper)s,\n" % field
    
    code2 = ""
    for field in fields:
        if 'field' not in field:
            code2 += "\tOF12PAT_%(action_upper)s_%(header_upper)s,\n" % field
            
    return skeleton % (code1, code2)
 
def generate_openflow_pipeline_action_c(fields):
    skeleton = read_template("of1x_action.c.template")  
    
    code1 = ""
    for field in fields:
        if 'field' not in field:
            code1 += "\t\tcase OF1X_AT_%(action_upper)s_%(header_upper)s:\n" % field
        else:
            code1 += "\t\tcase OF1X_AT_%(action_upper)s_FIELD_%(header_upper)s_%(field_upper)s:\n" % field
            
        code1 += "\t\t\taction->field.u%(length)s = field.u%(length)s&OF1X_%(masking)s_MASK;\n" % field
        code1 += "\t\t\taction->ver_req.min_ver = OF_VERSION_12;\n"
        code1 += "\t\t\tbreak;\n"
    
    code2 = ""
    for field in fields:
        if 'field' not in field:
            code2 += "\t\tcase OF1X_AT_%(action_upper)s_%(header_upper)s:\n" % field
            code2 += "\t\t\tplatform_packet_%(action)s_%(header)s(pkt, action->field.u%(length)s);\n" % field
            code2 += "\t\t\tpkt_matches->eth_type= platform_packet_get_eth_type(pkt);\n" % field
            code2 += "\t\t\tpkt_matches->pkt_size_bytes = platform_packet_get_size_bytes(pkt);\n" % field
        else:
            code2 += "\t\tcase OF1X_AT_%(action_upper)s_FIELD_%(header_upper)s_%(field_upper)s:\n" % field
            code2 += "\t\t\tplatform_packet_set_%(header)s_%(field)s(pkt, action->field.u%(length)s);\n" % field
            code2 += "\t\t\tpkt_matches->%(header)s_%(field)s = action->field.u%(length)s;\n" % field
        code2 += "\t\t\tbreak;\n"      
        
    code3 = ""
    for field in fields:
        if 'field' not in field:
            code3 += """\t\tcase OF1X_AT_%(action_upper)s_%(header_upper)s: ROFL_PIPELINE_DEBUG_NO_PREFIX("%(action_upper)s_%(header_upper)s"); \n""" % field
        else:
            code3 += """\t\tcase OF1X_AT_%(action_upper)s_FIELD_%(header_upper)s_%(field_upper)s: \n""" % field
            code3 += """\t\t\tROFL_PIPELINE_DEBUG_NO_PREFIX("%(action_upper)s_%(header_upper)s_%(field_upper)s: 0x%%x",action.field.u%(length)s); \n""" % field
        code3 += "\t\t\tbreak;\n"    

    return skeleton % (code1, code2, code3)
    

def generate_datapath_pipeline_platform_actions_h(fields):
    skeleton = read_template("packet_actions.h.template")  
    
    code = ""
    for field in fields:
        if 'field' not in field:
            code += "void platform_packet_%(action)s_%(header)s(datapacket_t* pkt, uint16_t ether_type);\n" % field # TODO
    return skeleton % code

    
def generate_rofl_actions(fields):
    rofl_pipeline_files_dir = ROFL_DIR + '/rofl-core/src/rofl/datapath/pipeline/openflow/openflow1x/pipeline/'
    generate_file(rofl_pipeline_files_dir + '/of1x_action.h', generate_openflow_pipeline_action_h(fields))
    generate_file(rofl_pipeline_files_dir + '/of1x_action.c', generate_openflow_pipeline_action_c(fields))
    
    generate_file(ROFL_DIR + '/rofl-core/src/rofl/datapath/pipeline/platform/packet_actions_autogenerated.h', generate_datapath_pipeline_platform_actions_h(fields))

    
generate_rofl_actions([{'header': 'pad_tag', 'action':'pop', 'length': '32'}, 
                               {'header': 'pad_tag', 'action':'push', 'length': '32'}, 
                               {'header': 'pad_tag', 'field':'a', 'length':'8', 'action':'set'},
                               {'header': 'pad_tag', 'field':'b', 'length':'16', 'action':'set'}])