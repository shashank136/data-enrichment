import pandas as pd
import glob
import phpserialize

# define similarly
def listing_street_view_location(lat, lng):
    dict = {};
    dict["latitude"] = str(lat);
    dict["longitude"] = str(lng);
    dict["zoom"] = "1";
    dict["heading"] = "-18";
    dict["pitch"] = "25";
    serializedString = phpserialize.serialize(dict);
    return serializedString;

files_li = glob.glob("./output/processed_*.csv")  # update path here
fields = ['lat', 'lng']  # for filling lat and lng

count = 1
for file in files_li:

    csv_input = ''
    csv_input = pd.read_csv(file)

    ###############
    # adding cols #
    ###############
    csv_input['listing_banner_map_marker'] = 'on'
    csv_input['listing_banner_map_type'] = 'ROADMAP'
    csv_input['listing_banner_map_zoom'] = '16'
    csv_input['listing_banner'] = 'banner_map'
    # csv_input['listing_inside_view_location_latitude'] = csv_input['lat']
    # csv_input['listing_inside_view_location_longitude'] = csv_input['lng']
    # csv_input['listing_inside_view_location_zoom'] = '16'
    # csv_input['listing_google_street_view_latitude'] = csv_input['lat']
    # csv_input['listing_google_street_view_longitude'] = csv_input['lng']
    # csv_input['listing_google_street_view_zoom'] = '16'
    # csv_input['listing_banner_street_view_latitude'] = csv_input['lat']
    # csv_input['listing_banner_street_view_longitude'] = csv_input['lng']
    csv_input['listing_banner_street_view_zoom'] = '16'
    csv_input['post_name'] = csv_input['Name']  # TO assign values of 1 col to new col
    csv_input['listing_description'] = csv_input['Details']  # TO assign values of 1 col to new col
    csv_input['listing_address'] = csv_input['fullAddress']
    csv_input['listing_email'] = csv_input['Mail']
    csv_input['listing_featured_image'] = csv_input['featured_image']
    csv_input['listing_gallery'] = csv_input['Images URL']
    csv_input['listing_map_location_latitude'] = csv_input['lat']
    csv_input['listing_map_location_longitude'] = csv_input['lng']
    csv_input['listing_map_location_zoom'] = '16'
    csv_input['listing_phone'] = csv_input['Phone1']
    # csv_input['listing_street_view_location'] = csv_input['fullAddress']
    # csv_input['listing_street_view_latitude'] = csv_input['lat']
    # csv_input['listing_street_view_longitude'] = csv_input['lng']
    # csv_input['listing_street_view_zoom'] = '16'
    # csv_input['listing_street_view_location_latitude'] = csv_input['lat']
    # csv_input['listing_street_view_location_longitude'] = csv_input['lng']
    # csv_input['listing_street_view_location_zoom'] = '16'
    csv_input['listing_type_metabox'] = csv_input['Services Offered']
    csv_input['locations'] = csv_input['listing_locations']

    # csv_input['post_category'] = csv_input['Services Offered']
    # csv_input['post_tag'] = csv_input['Services Offered']
    # csv_input['listing_categories'] = csv_input['Services Offered']

    ############
    # renaming #
    ############
    csv_input.rename(columns={
        'Name': 'post_title',
        'Details': 'post_content',
        'Mail': 'claim_email',
        'Phone1': 'claim_phone',
        'Working Hours': 'listing_opening_hours',
        'Website': 'listing_website'
        ###phone
        ###listing_description
        # 'Address'

    }, inplace=True)

    print(count)
    count += 1

    ##################################################
    # create lists here same no. as cols to be added #
    ##################################################
    li1 = [];
    li2 = []

    print(file + ' -> ' + 'updated_' + file[file.find('processed_') + 10:]);

    # print csv_input.keys()
    for x in range(len(csv_input.lat)):
        ####################
        # create col first #
        ####################
        csv_input['listing_banner_street_view'] = ''
        csv_input['listing_street_view_location'] = ''

        #############################
        # call functions from here  #
        #############################
        li1.append(listing_street_view_location(csv_input.lat[x], csv_input.lng[x]))
        li2.append(listing_street_view_location(csv_input.lat[x], csv_input.lng[x]))
    # csv_input.loc[ x ,'listing_banner_street_view'] = listing_banner_street_view(csv_input.lat[x], csv_input.lng[x])

    #######################
    # finally change here #
    #######################
    for x in range(len(li1)):
        csv_input.loc[x, 'listing_banner_street_view'] = li1[x]
        csv_input.loc[x, 'listing_street_view_location'] = li2[x]

    # Continue addtion of entries
    # csv_input['listing_google_street_view'] = csv_input['listing_banner_street_view']
    # csv_input['listing_inside_view_location'] = csv_input['listing_banner_street_view']
    csv_input['listing_map_location'] = csv_input['listing_banner_street_view']
    csv_input['listing_street_view'] = 'on'
    listing_map_location_address = csv_input['fullAddress']
    '''
    # check values of col using this
    for y in csv_input.listing_banner_street_view:
        print y
        print '\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n'
    '''
    csv_input.to_csv('./output/updated_' + file[file.find('processed_') + 10:], index=False)

