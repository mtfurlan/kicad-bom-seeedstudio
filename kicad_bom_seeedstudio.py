#!/usr/bin/env python3
import csv
import sys
import xml.etree.ElementTree as ET

### Natural key sorting for orders like : C1, C5, C10, C12 ... (instead of C1, C10, C12, C5...)
# http://stackoverflow.com/a/5967539
import re

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]
###

def parse_kicad_xml(input_file):
    """Parse the KiCad XML file and look for the part designators
    as done in the case of the official KiCad Open Parts Library:
    * OPL parts are designated with "SEED_SKU" (preferred)
    * other parts are designated with "MPN" and "DK_Details_Page"
    """
    components = {}
    parts = {}
    missing = []

    tree = ET.parse(input_file)
    root = tree.getroot()
    for f in root.findall('./components/'):
        ref = f.attrib['ref']
        info = {}
        fields = f.find('fields')
        opl, mpn, link = None, None, None
        if fields is not None:
            for x in fields:
                if x.attrib['name'].upper() == 'SEED_SKU':
                    opl = x.text
                elif x.attrib['name'].upper() == 'MPN':
                    mpn = x.text
                elif x.attrib['name'].upper() == 'DK_DETAIL_PAGE':
                    link = x.text

        if opl:
            components[ref] = {}
            components[ref]['part'] = opl
            components[ref]['link'] = "seeed OPL"
        elif mpn:
            components[ref] = {}
            components[ref]['part']= mpn
            components[ref]['link']= link
        else:
            missing += [ref]
            continue
    return components, missing

def write_bom_seeed(output_file_slug, components):
    """Write the BOM according to the Seeed Studio Fusion PCBA template available at:
    https://statics3.seeedstudio.com/files/20194/BOM%20Template.xlsx

    ```
    Designator,      Manufacturer Part Number or Seeed SKU,Qty,Link
    "C1,C2,C3,C4,C5",RHA0J471MCN1GS,                       5,  https://www.digikey.com.cn/product-detail/zh/nichicon/RHA0J471MCN1GS/493-3771-1-ND/2209480?keywords=RHA0J471MCN1GS
    "A1,A4",         RH0111-30002,                         2,  https://statics3.seeedstudio.com/images/opl/datasheet/318020010.pdf
    D1,              CYBLE-014008-00,                      1,  https://www.digikey.com.cn/product-detail/zh/cypress-semiconductor-corp/CYBLE-014008-00/428-3600-1-ND/6052585?keywords=CYBLE-014008-00
    ```

    The output is a CSV file at the `output_file_slug`.csv location.
    """
    parts = {}
    for ref in components:
        if components[ref]['part'] not in parts:
            parts[components[ref]['part']] = { 'link': components[ref]['link'], 'designators': []}
        parts[components[ref]['part']]['designators'].append(ref)

    field_names = ['Part/Designator', 'Manufacture Part Number/Seeed SKU', 'Quantity', 'Link']
    with open("{}.csv".format(output_file_slug), 'w') as csvfile:
        bomwriter = csv.DictWriter(csvfile, fieldnames=field_names, delimiter=',',
                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
        bomwriter.writeheader()
        for p in sorted(parts.keys()):
            pieces = sorted(parts[p]['designators'], key=natural_keys)
            designators = ",".join(pieces)
            bomwriter.writerow({'Part/Designator': designators,
                                'Manufacture Part Number/Seeed SKU': p,
                                'Quantity': len(pieces),
                                'Link': parts[p]['link']})


if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    components, missing = parse_kicad_xml(input_file)
    write_bom_seeed(output_file, components)
    if len(missing) > 0:
        print("** Warning **: there were parts with missing SKU/MFP")
        print(missing)
