import json
import os
import psycopg2
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def create_executing_bd_606_table():
    """Create the executing_bd_606 table if it doesn't exist"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create table SQL with all the necessary columns
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS executing_bd_606 (
            id SERIAL PRIMARY KEY,
            executing_bd VARCHAR(255),
            stock_group VARCHAR(255),
            month INTEGER,
            year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_type VARCHAR(50),
            ndoPct TEXT,
            ndoMarketPct TEXT,
            ndoMarketableLimitPct TEXT,
            ndoNonMarketableLimitPct TEXT,
            ndoOtherPct TEXT,
            venues VARCHAR(255),
            orderPct DECIMAL(15,6),
            marketPct DECIMAL(15,6),
            marketableLimitPct DECIMAL(15,6),
            nonMarketableLimitPct DECIMAL(15,6),
            otherPct DECIMAL(15,6),
            netpmtpaidrecvmarketordersusd DECIMAL(15,2),
            netpmtpaidrecvmarketorderscph DECIMAL(15,2),
            netpmtpaidrecvmarketablelimitordersusd DECIMAL(15,2),
            netpmtpaidrecvmarketablelimitorderscph DECIMAL(15,2),
            netpmtpaidrecvnonmarketablelimitordersusd DECIMAL(15,2),
            netpmtpaidrecvnonmarketablelimitorderscph DECIMAL(15,2),
            netpmtpaidrecvotherordersusd DECIMAL(15,2),
            netpmtpaidrecvotherorderscph DECIMAL(15,2),
            materialaspects TEXT
        )
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        logger.info("✅ Successfully created/verified executing_bd_606 table")
        
        # Create indexes for better performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_executing_bd_606_bd ON executing_bd_606(executing_bd)",
            "CREATE INDEX IF NOT EXISTS idx_executing_bd_606_stock_group ON executing_bd_606(stock_group)",
            "CREATE INDEX IF NOT EXISTS idx_executing_bd_606_year_month ON executing_bd_606(year, month)",
            "CREATE INDEX IF NOT EXISTS idx_executing_bd_606_data_type ON executing_bd_606(data_type)",
            "CREATE INDEX IF NOT EXISTS idx_executing_bd_606_venues ON executing_bd_606(venues)"
        ]
        
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
        
        conn.commit()
        logger.info("✅ Successfully created/verified indexes for executing_bd_606 table")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"💥 Failed to create executing_bd_606 table: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def download_xml_from_local(file_path):
    """Download XML file from local directory and return its content"""
    try:
        logger.info(f"Reading XML file from local path: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read the file content with encoding fallbacks
        encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16le', 'utf-16be']
        xml_content = None
        last_error = None
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as file:
                    xml_content = file.read()
                    logger.info(f"Successfully decoded file using encoding: {enc}")
                    break
            except UnicodeDecodeError as e:
                last_error = e
                continue
        
        if xml_content is None:
            # Final attempt: read binary and decode ignoring errors (preserve best-effort text)
            with open(file_path, 'rb') as file:
                data = file.read()
                try:
                    xml_content = data.decode('utf-8', errors='ignore')
                    logger.warning("Decoded with utf-8 ignoring errors as last resort")
                except Exception:
                    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Failed to decode using fallbacks; last error: {last_error}")
        
        logger.info(f"Successfully read {len(xml_content)} characters from local file")
        return xml_content
    except Exception as e:
        logger.error(f"Failed to read file from local directory: {str(e)}")
        raise

def parse_xml(xml_content):
    """Parse the XML content and extract relevant data"""
    try:
        logger.info(f"Parsing XML content of length: {len(xml_content)}")
        
        root = ET.fromstring(xml_content)
        ndo_rows = []
        venue_rows = []
        
        # Extract metadata directly from the expected structure
        bd_value = None
        bd_elem = root.find("./bd")
        if bd_elem is not None and bd_elem.text:
            bd_value = bd_elem.text
            logger.info(f"Found BD value: {bd_value}")

        qtr_value = None
        qtr_elem = root.find("./qtr")
        if qtr_elem is not None and qtr_elem.text:
            qtr_value = qtr_elem.text
            logger.info(f"Found QTR value: {qtr_value}")
        


        # Process each monthly report section
        for monthly_elem in root.findall("./rMonthly"):
            # Get year and month
            year_value = None
            month_value = None
            
            year_elem = monthly_elem.find("./year")
            if year_elem is not None and year_elem.text:
                try:
                    year_value = int(year_elem.text)
                    logger.info(f"Found year value: {year_value}")
                except (ValueError, TypeError):
                    # If we can't get year from monthly section, try the root
                    root_year = root.find("./year")
                    if root_year is not None and root_year.text:
                        try:
                            year_value = int(root_year.text)
                            logger.info(f"Found year value from root: {year_value}")
                        except (ValueError, TypeError):
                            year_value = datetime.now().year
                            logger.info(f"Using current year: {year_value}")
            
            mon_elem = monthly_elem.find("./mon")
            if mon_elem is not None and mon_elem.text:
                try:
                    month_value = int(mon_elem.text)
                    logger.info(f"Found month value: {month_value}")
                except (ValueError, TypeError):
                    logger.warning("Could not parse month value")
                    continue  # Skip this monthly report if no month
            
            if year_value is None or month_value is None:
                logger.warning("Missing year or month, skipping this monthly report")
                continue
            
            # Process SP500 stocks
            sp500_elem = monthly_elem.find("./rSP500")
            if sp500_elem is not None:
                ndoPct_value = None
                ndoPct_elem = sp500_elem.find("./ndoPct")
                if ndoPct_elem is not None and ndoPct_elem.text:
                    ndoPct_value = ndoPct_elem.text
                    logger.info(f"Found NdoPct value: {ndoPct_value}")

                ndoMarketPct_value = None
                ndoMarketPct_elem = sp500_elem.find("./ndoMarketPct")
                if ndoMarketPct_elem is not None and ndoMarketPct_elem.text:
                    ndoMarketPct_value = ndoMarketPct_elem.text
                    logger.info(f"Found ndoMarketPct value: {ndoMarketPct_value}")

                ndoMarketableLimitPct_value = None
                ndoMarketableLimitPct_elem = sp500_elem.find("./ndoMarketableLimitPct")
                if ndoMarketableLimitPct_elem is not None and ndoMarketableLimitPct_elem.text:
                    ndoMarketableLimitPct_value = ndoMarketableLimitPct_elem.text
                    logger.info(f"Found ndoMarketableLimitPct value: {ndoMarketableLimitPct_value}")

                ndoNonMarketableLimitPct_value = None
                ndoNonMarketableLimitPct_elem = sp500_elem.find("./ndoNonMarketableLimitPct")
                if ndoNonMarketableLimitPct_elem is not None and ndoNonMarketableLimitPct_elem.text:
                    ndoNonMarketableLimitPct_value = ndoNonMarketableLimitPct_elem.text
                    logger.info(f"Found ndoNonMarketableLimitPct value: {ndoNonMarketableLimitPct_value}")

                ndoOtherPct_value = None
                ndoOtherPct_elem = sp500_elem.find("./ndoOtherPct")
                if ndoOtherPct_elem is not None and ndoOtherPct_elem.text:
                    ndoOtherPct_value = ndoOtherPct_elem.text
                    logger.info(f"Found ndoOtherPct value: {ndoOtherPct_value}")

                # Create NDO row for SP500
                ndo_row = create_ndo_row(
                    executing_bd=bd_value,
                    stock_group="SP500",
                    month=month_value,
                    year=year_value,
                    ndoPct=ndoPct_value,
                    ndoMarketPct=ndoMarketPct_value,
                    ndoMarketableLimitPct=ndoMarketableLimitPct_value,
                    ndoNonMarketableLimitPct=ndoNonMarketableLimitPct_value,
                    ndoOtherPct=ndoOtherPct_value
                )
                ndo_rows.append(ndo_row)

                # Look for rVenues section
                r_venues_section = sp500_elem.find("./rVenues")
                if r_venues_section is not None:
                    # Find all rVenue elements inside rVenues
                    r_venue_elements = r_venues_section.findall("./rVenue")
                    logger.info(f"Found {len(r_venue_elements)} rVenue elements in SP500/rVenues section")
                    
                    # Process each rVenue element
                    for r_venue_elem in r_venue_elements:
                        row = process_r_venue(r_venue_elem, "SP500", bd_value, month_value, year_value)
                        if row:
                            venue_rows.append(row)
                    
                    logger.info(f"Added {len(r_venue_elements)} venue rows for SP500")
                else:
                    logger.info("No rVenues section found in SP500 section")
            
            # Process Options 
            options_elem = monthly_elem.find("./rOptions")
            if options_elem is not None:
                # Extract Options-specific ndo values
                ndoPct_value = None
                ndoPct_elem =  options_elem.find("./ndoPct")
                if ndoPct_elem is not None and ndoPct_elem.text:
                    ndoPct_value = ndoPct_elem.text
                    logger.info(f"Found Options NdoPct value: {ndoPct_value}")

                ndoMarketPct_value = None
                ndoMarketPct_elem = options_elem.find("./ndoMarketPct")
                if ndoMarketPct_elem is not None and ndoMarketPct_elem.text:
                    ndoMarketPct_value = ndoMarketPct_elem.text
                    logger.info(f"Found Options ndoMarketPct value: {ndoMarketPct_value}")

                ndoMarketableLimitPct_value = None
                ndoMarketableLimitPct_elem = options_elem.find("./ndoMarketableLimitPct")
                if ndoMarketableLimitPct_elem is not None and ndoMarketableLimitPct_elem.text:
                    ndoMarketableLimitPct_value = ndoMarketableLimitPct_elem.text
                    logger.info(f"Found Options ndoMarketableLimitPct value: {ndoMarketableLimitPct_value}")

                ndoNonMarketableLimitPct_value = None
                ndoNonMarketableLimitPct_elem = options_elem.find("./ndoNonMarketableLimitPct")
                if ndoNonMarketableLimitPct_elem is not None and ndoNonMarketableLimitPct_elem.text:
                    ndoNonMarketableLimitPct_value = ndoNonMarketableLimitPct_elem.text
                    logger.info(f"Found Options ndoNonMarketableLimitPct value: {ndoNonMarketableLimitPct_value}")

                ndoOtherPct_value = None
                ndoOtherPct_elem = options_elem.find("./ndoOtherPct")
                if ndoOtherPct_elem is not None and ndoOtherPct_elem.text:
                    ndoOtherPct_value = ndoOtherPct_elem.text
                    logger.info(f"Found Options ndoOtherPct value: {ndoOtherPct_value}")

                # Create NDO row for Options
                ndo_row = create_ndo_row(
                    executing_bd=bd_value,
                    stock_group="Options",
                    month=month_value,
                    year=year_value,
                    ndoPct=ndoPct_value,
                    ndoMarketPct=ndoMarketPct_value,
                    ndoMarketableLimitPct=ndoMarketableLimitPct_value,
                    ndoNonMarketableLimitPct=ndoNonMarketableLimitPct_value,
                    ndoOtherPct=ndoOtherPct_value
                )
                ndo_rows.append(ndo_row)

                # Look for rVenues section
                r_venues_section = options_elem.find("./rVenues")
                if r_venues_section is not None:
                    # Find all rVenue elements inside rVenues
                    r_venue_elements = r_venues_section.findall("./rVenue")
                    logger.info(f"Found {len(r_venue_elements)} rVenue elements in Options/rVenues section")

                    # Process each rVenue element
                    for r_venue_elem in r_venue_elements:
                        row = process_r_venue(r_venue_elem, "Options", bd_value, month_value, year_value)
                        if row:
                            venue_rows.append(row)
                    
                    logger.info(f"Added {len(r_venue_elements)} venue rows for Options")
                else:
                    logger.info("No rVenues section found in Options section")

            # Process Other Stocks
            other_stocks_elem = monthly_elem.find("./rOtherStocks")
            if other_stocks_elem is not None:
                # Extract OtherStocks-specific ndo values
                ndoPct_value = None
                ndoPct_elem = other_stocks_elem.find("./ndoPct")
                if ndoPct_elem is not None and ndoPct_elem.text:
                    ndoPct_value = ndoPct_elem.text
                    logger.info(f"Found OtherStocks NdoPct value: {ndoPct_value}")

                ndoMarketPct_value = None
                ndoMarketPct_elem = other_stocks_elem.find("./ndoMarketPct")
                if ndoMarketPct_elem is not None and ndoMarketPct_elem.text:
                    ndoMarketPct_value = ndoMarketPct_elem.text
                    logger.info(f"Found OtherStocks ndoMarketPct value: {ndoMarketPct_value}")

                ndoMarketableLimitPct_value = None
                ndoMarketableLimitPct_elem = other_stocks_elem.find("./ndoMarketableLimitPct")
                if ndoMarketableLimitPct_elem is not None and ndoMarketableLimitPct_elem.text:
                    ndoMarketableLimitPct_value = ndoMarketableLimitPct_elem.text
                    logger.info(f"Found OtherStocks ndoMarketableLimitPct value: {ndoMarketableLimitPct_value}")

                ndoNonMarketableLimitPct_value = None
                ndoNonMarketableLimitPct_elem = other_stocks_elem.find("./ndoNonMarketableLimitPct")
                if ndoNonMarketableLimitPct_elem is not None and ndoNonMarketableLimitPct_elem.text:
                    ndoNonMarketableLimitPct_value = ndoNonMarketableLimitPct_elem.text
                    logger.info(f"Found OtherStocks ndoNonMarketableLimitPct value: {ndoNonMarketableLimitPct_value}")

                ndoOtherPct_value = None
                ndoOtherPct_elem = other_stocks_elem.find("./ndoOtherPct")
                if ndoOtherPct_elem is not None and ndoOtherPct_elem.text:
                    ndoOtherPct_value = ndoOtherPct_elem.text
                    logger.info(f"Found OtherStocks ndoOtherPct value: {ndoOtherPct_value}")

                # Create NDO row for OtherStocks
                ndo_row = create_ndo_row(
                    executing_bd=bd_value,
                    stock_group="OtherStocks",
                    month=month_value,
                    year=year_value,
                    ndoPct=ndoPct_value,
                    ndoMarketPct=ndoMarketPct_value,
                    ndoMarketableLimitPct=ndoMarketableLimitPct_value,
                    ndoNonMarketableLimitPct=ndoNonMarketableLimitPct_value,
                    ndoOtherPct=ndoOtherPct_value
                )
                ndo_rows.append(ndo_row)

                # Look for rVenues section
                r_venues_section = other_stocks_elem.find("./rVenues")
                if r_venues_section is not None:
                    # Find all rVenue elements inside rVenues
                    r_venue_elements = r_venues_section.findall("./rVenue")
                    logger.info(f"Found {len(r_venue_elements)} rVenue elements in OtherStocks/rVenues section")
                    
                    # Process each rVenue element
                    for r_venue_elem in r_venue_elements:
                        row = process_r_venue(r_venue_elem, "OtherStocks", bd_value, month_value, year_value)
                        if row:
                            venue_rows.append(row)
        
                    logger.info(f"Added {len(r_venue_elements)} venue rows for OtherStocks")
                else:
                    logger.info("No rVenues section found in OtherStocks section")
                    
        logger.info(f"Total extracted NDO rows: {len(ndo_rows)}")
        logger.info(f"Total extracted venue rows: {len(venue_rows)}")
        return ndo_rows, venue_rows
    except ET.ParseError as e:
        logger.error(f"Error parsing XML: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during XML parsing: {e}")
        raise

def process_r_venue(r_venue_elem, stock_group_name, executing_bd, month_value, year_value):
    """Process a single rVenue element and return venue data"""
    # Extract venue name
    venue_name = get_text_from_element(r_venue_elem, "name")
    
    logger.debug(f"Processing venue: {venue_name}")
    
    # Extract venue-specific percentages
    venue_orderPct = get_float_value_from_element(r_venue_elem, "orderPct")
    venue_marketPct = get_float_value_from_element(r_venue_elem, "marketPct")
    venue_marketableLimitPct = get_float_value_from_element(r_venue_elem, "marketableLimitPct")
    venue_nonMarketableLimitPct = get_float_value_from_element(r_venue_elem, "nonMarketableLimitPct")
    venue_otherPct = get_float_value_from_element(r_venue_elem, "otherPct")
    
    # Extract payment values
    net_market_usd = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvMarketOrdersUsd")
    net_market_cph = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvMarketOrdersCph")
    net_marketable_limit_usd = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvMarketableLimitOrdersUsd")
    net_marketable_limit_cph = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvMarketableLimitOrdersCph")
    net_non_marketable_limit_usd = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvNonMarketableLimitOrdersUsd")
    net_non_marketable_limit_cph = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvNonMarketableLimitOrdersCph")
    net_other_usd = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvOtherOrdersUsd")
    net_other_cph = get_float_value_from_element(r_venue_elem, "netPmtPaidRecvOtherOrdersCph")
    
    # Material aspects
    material_aspects = get_text_from_element(r_venue_elem, "materialAspects") or ""
    
    row = create_venue_row(
        executing_bd=executing_bd,
        month=month_value,
        year=year_value,
        stock_group=stock_group_name,
        venues=venue_name,
        orderPct=venue_orderPct,
        marketPct=venue_marketPct,
        marketableLimitPct=venue_marketableLimitPct,
        nonMarketableLimitPct=venue_nonMarketableLimitPct,
        otherPct=venue_otherPct,
        netpmtpaidrecvmarketordersusd=net_market_usd,
        netpmtpaidrecvmarketorderscph=net_market_cph,
        netpmtpaidrecvmarketablelimitordersusd=net_marketable_limit_usd,
        netpmtpaidrecvmarketablelimitorderscph=net_marketable_limit_cph,
        netpmtpaidrecvnonmarketablelimitordersusd=net_non_marketable_limit_usd,
        netpmtpaidrecvnonmarketablelimitorderscph=net_non_marketable_limit_cph,
        netpmtpaidrecvotherordersusd=net_other_usd,
        netpmtpaidrecvotherorderscph=net_other_cph,
        materialaspects=material_aspects
    )
    
    return row

def get_text_from_element(element, tag_name):
    """Get text content from a child element with the given tag name"""
    child = element.find(f"./{tag_name}")
    if child is not None and child.text:
        return child.text.strip()
    return ""

def get_float_value_from_element(element, tag_name):
    """Get float value from a child element with the given tag name"""
    child = element.find(f"./{tag_name}")
    if child is not None and child.text:
        # Remove any non-numeric characters except for decimal point
        value = re.sub(r'[^\d.]+', '', child.text)
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0
def create_ndo_row(executing_bd, stock_group, month, year, ndoPct, ndoMarketPct, ndoMarketableLimitPct, ndoNonMarketableLimitPct, ndoOtherPct):
    """Create an NDO data row (first type)"""
    row = {
        "executing_bd": executing_bd,
        "stock_group": stock_group,
        "month": month,
        "year": year,
        "created_at": datetime.now(),
        "data_type": "executing_bd",  # BD-level data
        "ndoPct": ndoPct,
        "ndoMarketPct": ndoMarketPct,
        "ndoMarketableLimitPct": ndoMarketableLimitPct,
        "ndoNonMarketableLimitPct": ndoNonMarketableLimitPct,
        "ndoOtherPct": ndoOtherPct
    }
    return row

def create_venue_row(executing_bd, month, year, stock_group, venues, orderPct, marketPct, marketableLimitPct, nonMarketableLimitPct, otherPct,
                    netpmtpaidrecvmarketordersusd, netpmtpaidrecvmarketorderscph,
                    netpmtpaidrecvmarketablelimitordersusd, netpmtpaidrecvmarketablelimitorderscph,
                    netpmtpaidrecvnonmarketablelimitordersusd, netpmtpaidrecvnonmarketablelimitorderscph,
                    netpmtpaidrecvotherordersusd, netpmtpaidrecvotherorderscph,
                    materialaspects):
    """Create a venue data row (second type)"""
    row = {
        "executing_bd": executing_bd,
        "month": month,
        "year": year,
        "stock_group": stock_group,
        "created_at": datetime.now(),
        "data_type": "venue" if venues else "executing_bd",
        "venues": venues,
        "orderPct": orderPct,
        "marketPct": marketPct,
        "marketableLimitPct": marketableLimitPct,
        "nonMarketableLimitPct": nonMarketableLimitPct,
        "otherPct": otherPct,
        "netpmtpaidrecvmarketordersusd": netpmtpaidrecvmarketordersusd,
        "netpmtpaidrecvmarketorderscph": netpmtpaidrecvmarketorderscph,
        "netpmtpaidrecvmarketablelimitordersusd": netpmtpaidrecvmarketablelimitordersusd,
        "netpmtpaidrecvmarketablelimitorderscph": netpmtpaidrecvmarketablelimitorderscph,
        "netpmtpaidrecvnonmarketablelimitordersusd": netpmtpaidrecvnonmarketablelimitordersusd,
        "netpmtpaidrecvnonmarketablelimitorderscph": netpmtpaidrecvnonmarketablelimitorderscph,
        "netpmtpaidrecvotherordersusd": netpmtpaidrecvotherordersusd,
        "netpmtpaidrecvotherorderscph": netpmtpaidrecvotherorderscph,
        "materialaspects": materialaspects
    }
    return row

def insert_into_db(all_rows, db_config=None):
    """Insert all data (both NDO and venue) into PostgreSQL database"""
    # Ensure table exists before inserting data
    create_executing_bd_606_table()
    
    if db_config is None:
        db_config = {
            "host": os.environ['DB_HOST'],
            "port": int(os.environ['DB_PORT']),
            "database": os.environ['DB_NAME'],
            "user": os.environ['DB_USER'],
            "password": os.environ['DB_PASSWORD']
        }

    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # SQL insert statement for all data types
        insert_sql = """
        INSERT INTO executing_bd_606 (
            executing_bd,
            stock_group,
            month,
            year,
            created_at,
            data_type,
            ndoPct,
            ndoMarketPct,
            ndoMarketableLimitPct,
            ndoNonMarketableLimitPct,
            ndoOtherPct,
            venues,
            orderPct,
            marketPct,
            marketableLimitPct,
            nonMarketableLimitPct,
            otherPct,
            netpmtpaidrecvmarketordersusd,
            netpmtpaidrecvmarketorderscph,
            netpmtpaidrecvmarketablelimitordersusd,
            netpmtpaidrecvmarketablelimitorderscph,
            netpmtpaidrecvnonmarketablelimitordersusd,
            netpmtpaidrecvnonmarketablelimitorderscph,
            netpmtpaidrecvotherordersusd,
            netpmtpaidrecvotherorderscph,
            materialaspects
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        inserted_count = 0
        for row in all_rows:
            values = (
                row.get('executing_bd') or None,
                row.get('stock_group') or None,
                row.get('month') or None,
                row.get('year') or None,
                row.get('created_at') or None,
                row.get('data_type') or None,
                row.get('ndoPct') or None,
                row.get('ndoMarketPct') or None,
                row.get('ndoMarketableLimitPct') or None,
                row.get('ndoNonMarketableLimitPct') or None,
                row.get('ndoOtherPct') or None,
                row.get('venues') or None,
                float(row['orderPct']) if row.get('orderPct') not in (None, "", "NA") else None,
                float(row['marketPct']) if row.get('marketPct') not in (None, "", "NA") else None,
                float(row['marketableLimitPct']) if row.get('marketableLimitPct') not in (None, "", "NA") else None,
                float(row['nonMarketableLimitPct']) if row.get('nonMarketableLimitPct') not in (None, "", "NA") else None,
                float(row['otherPct']) if row.get('otherPct') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvmarketordersusd']) if row.get('netpmtpaidrecvmarketordersusd') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvmarketorderscph']) if row.get('netpmtpaidrecvmarketorderscph') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvmarketablelimitordersusd']) if row.get('netpmtpaidrecvmarketablelimitordersusd') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvmarketablelimitorderscph']) if row.get('netpmtpaidrecvmarketablelimitorderscph') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvnonmarketablelimitordersusd']) if row.get('netpmtpaidrecvnonmarketablelimitordersusd') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvnonmarketablelimitorderscph']) if row.get('netpmtpaidrecvnonmarketablelimitorderscph') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvotherordersusd']) if row.get('netpmtpaidrecvotherordersusd') not in (None, "", "NA") else None,
                float(row['netpmtpaidrecvotherorderscph']) if row.get('netpmtpaidrecvotherorderscph') not in (None, "", "NA") else None,
                (row.get('materialaspects') or "")[:1000] or None
            )

            cursor.execute(insert_sql, values)
            inserted_count += 1

        conn.commit()
        logger.info(f"✅ Successfully inserted {inserted_count} records")
        return True, inserted_count

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"💥 Database insertion failed: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

            
def process_xml_file(file_path):
    """Process a single XML file and insert data into database"""
    try:
        logger.info(f"Processing XML file: {file_path}")
        
        # Check if it's an XML file
        if not file_path.lower().endswith('.xml'):
            raise ValueError(f"File is not an XML file: {file_path}")
        
        # Ensure table exists
        create_executing_bd_606_table()
        
        # Read XML from local file
        xml_content = download_xml_from_local(file_path)
        
        # Parse XML
        logger.info("Parsing XML content")
        ndo_rows, venue_rows = parse_xml(xml_content)
        
        if not ndo_rows and not venue_rows:
            logger.warning(f"No data found in XML file: {file_path}")
            return {
                'file': file_path,
                'status': 'no_data',
                'records_processed': 0
            }
        
        # Combine both data types and insert into database
        all_rows = ndo_rows + venue_rows
        logger.info(f"Inserting {len(all_rows)} total records ({len(ndo_rows)} NDO + {len(venue_rows)} venue) into database")
        success, inserted_count = insert_into_db(all_rows)
        
        if success:
            logger.info(f"✅ Successfully processed {file_path}")
            return {
                'file': file_path,
                'status': 'success',
                'ndo_records_processed': len(ndo_rows),
                'venue_records_processed': len(venue_rows),
                'total_records_processed': len(all_rows),
                'total_records_inserted': inserted_count
            }
        else:
            logger.error(f"❌ Failed to insert data for {file_path}")
            return {
                'file': file_path,
                'status': 'failed',
                'error': 'Database insertion failed'
            }
            
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {str(e)}")
        return {
            'file': file_path,
            'status': 'error',
            'error': str(e)
        }

def process_xml_content(xml_content):
    """Process XML content directly and insert data into database"""
    try:
        logger.info("Processing direct XML content")
        
        # Ensure table exists
        create_executing_bd_606_table()
        
        # Parse XML
        logger.info("Parsing XML content")
        ndo_rows, venue_rows = parse_xml(xml_content)
        
        if not ndo_rows and not venue_rows:
            logger.warning("No data found in XML content")
            return {
                'status': 'no_data',
                'records_processed': 0
            }
        
        # Combine both data types and insert into database
        all_rows = ndo_rows + venue_rows
        logger.info(f"Inserting {len(all_rows)} total records ({len(ndo_rows)} NDO + {len(venue_rows)} venue) into database")
        success, inserted_count = insert_into_db(all_rows)
        
        if success:
            logger.info("✅ Successfully processed XML content")
            return {
                'status': 'success',
                'ndo_records_processed': len(ndo_rows),
                'venue_records_processed': len(venue_rows),
                'total_records_processed': len(all_rows),
                'total_records_inserted': inserted_count
            }
        else:
            logger.error("❌ Failed to insert data from XML content")
            return {
                'status': 'failed',
                'error': 'Database insertion failed'
            }
            
    except Exception as e:
        logger.error(f"Failed to process XML content: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python xml2localpostgres.py <xml_file_path>")
        print("   or: python xml2localpostgres.py --create-table")
        sys.exit(1)
    
    if sys.argv[1] == '--create-table':
        print("Creating table...")
        create_executing_bd_606_table()
        print("✅ Table created successfully!")
        return
    
    xml_file_path = sys.argv[1]
    result = process_xml_file(xml_file_path)
    
    print(f"Processing result: {json.dumps(result, indent=2)}")
    
    if result['status'] == 'success':
        print(f"✅ Successfully processed {xml_file_path}")
        print(f"   - NDO records: {result['ndo_records_processed']}")
        print(f"   - Venue records: {result['venue_records_processed']}")
        print(f"   - Total records: {result['total_records_processed']}")
        print(f"   - Inserted: {result['total_records_inserted']}")
    else:
        print(f"❌ Failed to process {xml_file_path}: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main() 