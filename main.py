#importing required libraries

import streamlit as st # for easy web dev (frontend + backend)
import requests # to get URL request as save the html file
from bs4 import BeautifulSoup # use for scraping static html
import pandas as pd # as we all know for DataFrame
import io # makes download ezpz

# setting the streamlit page orientation
st.set_page_config(page_title="Wikipedia Tabular Data Scraper",
                   layout="centered")

# ofcourse the title
st.title('Wikipedia Tabular Data Scraper')

# to mention my name and linkedIn URL (ofcourse someone will remove it to deploy in their machine but it's ok I learned a lot from this project)
# giving credit to me is all of your's choice as this code is open for all
st.link_button(label='Mekhma Tamang',url='https://www.linkedin.com/in/mekhma-tamang/', icon=":material/link:",type='tertiary', help='Visit my LinkedIn')


# user inputs wikipedia URL
wiki_url = st.text_input(label='Input Wikipedia URL below')

# handles the session_state which is really handy to parse the data from one func to another
if "tables" not in st.session_state:
    st.session_state.update({ # the update func allows the page to reset the session_state whenever the page is refresh manually
        "tables": [],
        "table_headings": {},
        "selected_df": None,
        "final_df": None,
        "table_title": None,
        "final_csv": None,
        "download_filename": None,
        "username": None,
        "password": None,
        "table_created": False,
        "form_submitted": False
    })

# creates the functions to fetch tables from url that returns tables and table_headings
def fetch_tables(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser') # using BeautifulSoup aahaa

    # finds all tables who have a class wikitable 
    # simply code extracts the table : class : names and within names search for wikitable which allows us to get into every tables
    # this method is finalize after understanding the patterns of table used by wikipedia (PS: went through 20 pages)
    tables = [
        table for table in soup.find_all('table')
        if table.has_attr('class') and any('wikitable' in cls for cls in table['class'])
    ]


    table_headings = {} # ofcourse dict to save headings relatively to the table. uff! this one was tough to track as no any heading mentioned in html tag of table
    current_heading = None

    # iterates over h2,h3 and table tags
    for tag in soup.find_all(['h2', 'h3', 'table']):
        if tag.name in ['h2', 'h3']: # save the h2 or h3 whichever comes last in current headings
            current_heading = tag.get_text(strip=True)
        elif tag.name == 'table' and tag in tables: # saved heading is for this table
            # basically h2 or h3 that are present above the tables are considered as table headings
            # this pattern is really amazing in wiki
            table_headings[tag] = current_heading or f"Table {len(table_headings) + 1}"

    return tables, table_headings

# whenever the fetch data button is clicked, tables are extracted
if st.button('Fetch Data', type='secondary', icon=":material/query_stats:"):
    if not wiki_url.startswith("http"): # this to handle some studs who tries jpt url like me 
        st.error("Please enter a valid Wikipedia URL.")
    else:
        # the code is totally for wikipedia, why? because the patterns are cracked for wiki only, other websites may have different patterns 
        tables, table_headings = fetch_tables(wiki_url)
        st.session_state.tables = tables
        st.session_state.table_headings = table_headings # see these session_state saves the variable life becomes ez

st.divider() # nth just a streamlit api func to create the divider in UI
col1, col2 = st.columns(2) # two columns for visualize

# in column 1 , we are displaying the table names that are clickable
with col1:
    if st.session_state.tables:
        for i, table in enumerate(st.session_state.tables):
            table_title = st.session_state.table_headings.get(table, f"Table {i+1}")

            if st.button(f"{i+1} : {table_title}", key=f'button_{i}', type="tertiary"):
                # extracts headings of table "th" bam
                headers = [th.text.strip() for th in table.find_all('th')] 

                # pandas in action first added headers
                df = pd.DataFrame(columns=headers)

                # skips the row 1 or row[0] which is our header, why this? to input the data skipping headers
                for row in table.find_all('tr')[1:]:
                    row_data = []
                    # each row data are present in "td"
                    cols = row.find_all('td')

                    # iterating through col name, why? because I extracted the <a href> for Image and Websites which makes scraper ezpz
                    for i, col in enumerate(cols):
                        header = headers[i] if i < len(headers) else ""

                        # Check if the column header is "Image" or "Website"
                        if header in ["Image", "Photo","Website"]:
                            a_tag = col.find('a')
                            href = (a_tag['href'].strip() if a_tag and a_tag.has_attr('href') else '')
                            if header == 'Image' or (header == 'Photo') and href:
                                row_data.append(f'https://en.wikipedia.org{href}')
                            if header == 'Website' and href:
                                row_data.append(f'{href}')
                        else:
                            row_data.append(col.text.strip())

                    # extending rows because sometimes the no: of headers are mismatched with row_data
                    row_data.extend([''] * (len(headers) - len(row_data)))

                    # inserts the data
                    df.loc[len(df)] = row_data[:len(headers)]
                    
                
                # see all below session_states are gonna handy for next func and also for downloading csv file
                st.session_state.selected_df = df.set_index(df.columns[0]).head(5)
                st.session_state.final_df = df
                st.session_state.table_title = table_title

                # download as csv
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.session_state.final_csv = csv_buffer.getvalue()

                # exact csv name as table_tile boom , you can recognize what you have downloaded 
                st.session_state.download_filename = f"{table_title.replace(' ', '_')}.csv"

# in column 2, we will preview data for user reference that makes user life ez
with col2:
    if st.session_state.selected_df is not None:

        # it shows the title and data
        st.subheader(st.session_state.table_title)
        st.dataframe(st.session_state.selected_df)

        # again 2 columns for download and postgresql buttons
        col3, col4 = st.columns(2)

        # download_CSV button baam!
        with col3:
            st.download_button(
                label="Download CSV",
                data=st.session_state.final_csv,
                file_name=st.session_state.download_filename,
                mime="text/csv"
            )