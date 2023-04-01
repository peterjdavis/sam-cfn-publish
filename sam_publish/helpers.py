import os

def get_cfn_parameter(search_item) -> any:
    for cfn_parameter in cfn_parameters:
        if cfn_parameter == search_item:
            item = cfn_parameters[cfn_parameter]
            return item

def resolve_element(cfn, element):
    if 'Ref' in element:
        item = get_cfn_parameter(element['Ref'])
        return item
    elif 'Fn::Sub' in element:
        items = element['Fn::Sub'].split('${')
        item = ''
        for sub_item in items:
            split_sub_item = sub_item.split('}')
            if len(split_sub_item) == 1:
                item = item + split_sub_item[0]
            else:
                item = item + \
                    get_cfn_parameter(split_sub_item[0]) + split_sub_item[1]
        return item
    else:
        return element

def get_filename_from_path(path):
    path_parts = path.split('/')
    return path_parts[len(path_parts) - 1]

def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path) 