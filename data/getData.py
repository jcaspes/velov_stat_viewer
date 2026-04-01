import requests
import sys
from pathlib import Path

# Get velo'v history data from https://data.grandlyon.com/fr/datapusher/ws/timeseries
# api call smaple https://data.grandlyon.com/fr/datapusher/ws/timeseries/jcd_jcdecaux.historiquevelov/all.csv?maxfeatures=370000&start=1&filename=stations-velo-v-de-la-metropole-de-lyon---disponibilites-temps-reel&field=number&value=30002
# parameter maxfeatures allow to define how many records we want
# parameter start allow to define starting record for pagination
# parameter value allow to define velo'v station id to retrieve
# record 1 start in mars 2023
# record 250000 is in april 2026
def fetch_velov_data(station_id, start_record, records_count):
	"""
	Fetch velo'v history data from the API and save to disk.
	
	Args:
		station_id: The velo'v station ID
		start_record: The starting record for pagination
		records_count: The number of records to retrieve
	"""
	url = "https://data.grandlyon.com/fr/datapusher/ws/timeseries/jcd_jcdecaux.historiquevelov/all.csv"
	params = {
		"maxfeatures": records_count,
		"start": start_record,
		"filename": "stations-velo-v-de-la-metropole-de-lyon---disponibilites-temps-reel",
		"field": "number",
		"value": station_id
	}
	
	response = requests.get(url, params=params)
	response.raise_for_status()
	
	filename = f"station_{station_id}_records_{records_count}.csv"
	Path(filename).write_text(response.text, encoding='utf-8')
	print(f"Data saved to {filename}")

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Usage: python getData.py <station_id> <records_count> [start_record]")
		sys.exit(1)
	
	station_id = sys.argv[1]
	records_count = int(sys.argv[2])
	start_record = int(sys.argv[3]) if len(sys.argv) > 3 else 1
	fetch_velov_data(station_id, start_record, records_count)



