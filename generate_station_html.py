import argparse
import ast
import csv
import json
from datetime import datetime
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Station {station_number} - Vélo'v status</title>
    <script src="https://cdn.plot.ly/plotly-2.31.1.min.js"></script>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; background: #f5f5f5; color: #222; }}
        .container {{ max-width: 1200px; margin: 24px auto; padding: 0 18px; }}
        h1 {{ margin: 0 0 14px; font-size: 1.9rem; }}
        .controls {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 16px; }}
        .controls label {{ display: flex; flex-direction: column; font-size: 0.95rem; }}
        .controls input {{ padding: 8px 10px; border: 1px solid #bbb; border-radius: 6px; min-width: 220px; }}
        .controls button {{ padding: 10px 16px; border: none; background: #0078d4; color: white; border-radius: 6px; cursor: pointer; }}
        .controls button:hover {{ background: #005ea8; }}
        #graph {{ width: 100%; min-height: 640px; background: white; border-radius: 10px; box-shadow: 0 0 18px rgba(0, 0, 0, 0.08); }}
        .description {{ margin: 0 0 12px; color: #444; font-size: 0.95rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Station {station_number}</h1>
        <div class="description">Lines: capacity, bikes, stands, electricalBikes, mechanicalBikes. Status bars are green for OPEN and red for CLOSED.</div>
        <div class="controls">
            <label>Start date
                <input id="startDate" type="datetime-local" />
            </label>
            <label>End date
                <input id="endDate" type="datetime-local" />
            </label>
            <button id="zoomButton">Zoom</button>
            <button id="resetButton">Reset view</button>
        </div>
        <div id="graph"></div>
    </div>

    <script>
        const data = {data_json};
        const statusColors = {status_colors};
        const stationNumber = "{station_number}";

        const traces = [
            {{
                x: data.timestamps,
                y: data.capacity,
                name: 'capacity',
                mode: 'lines+markers',
                line: {{ width: 2, color: '#1f77b4' }},
                marker: {{ size: 6 }},
                hovertemplate: '%{{x}}<br>capacity: %{{y}}<extra></extra>',
            }},
            {{
                x: data.timestamps,
                y: data.bikes,
                name: 'bikes',
                mode: 'lines+markers',
                line: {{ width: 2, dash: 'dashdot', color: '#ff7f0e' }},
                marker: {{ size: 6 }},
                hovertemplate: '%{{x}}<br>bikes: %{{y}}<extra></extra>',
            }},
            {{
                x: data.timestamps,
                y: data.stands,
                name: 'stands',
                mode: 'lines+markers',
                line: {{ width: 2, dash: 'dot', color: '#2ca02c' }},
                marker: {{ size: 6 }},
                hovertemplate: '%{{x}}<br>stands: %{{y}}<extra></extra>',
            }},
            {{
                x: data.timestamps,
                y: data.electricalBikes,
                name: 'electricalBikes',
                mode: 'lines+markers',
                line: {{ width: 2, dash: 'dash', color: '#d62728' }},
                marker: {{ size: 6 }},
                hovertemplate: '%{{x}}<br>electricalBikes: %{{y}}<extra></extra>',
            }},
            {{
                x: data.timestamps,
                y: data.mechanicalBikes,
                name: 'mechanicalBikes',
                mode: 'lines+markers',
                line: {{ width: 2, dash: 'longdash', color: '#9467bd' }},
                marker: {{ size: 6 }},
                hovertemplate: '%{{x}}<br>mechanicalBikes: %{{y}}<extra></extra>',
            }},
            {{
                x: data.timestamps,
                y: data.status_values,
                name: 'status',
                type: 'bar',
                marker: {{ color: data.status_colors, line: {{ width: 0 }} }},
                yaxis: 'y2',
                hovertemplate: '%{{x}}<br>status: %{{customdata}}<extra></extra>',
                customdata: data.status_labels,
                opacity: 0.6,
            }},
        ];

        const layout = {{
            title: {{ text: 'Station ' + stationNumber, x: 0.01, xanchor: 'left' }},
            legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.08, xanchor: 'left', x: 0 }},
            margin: {{ t: 80, b: 80, l: 70, r: 70 }},
            xaxis: {{
                title: 'Date',
                type: 'date',
                rangeslider: {{ visible: true }},
                rangeselector: {{
                    buttons: [
                        {{ step: 'day', count: 1, label: '1d' }},
                        {{ step: 'day', count: 7, label: '7d' }},
                        {{ step: 'month', count: 1, label: '1m' }},
                        {{ step: 'all', label: 'All' }},
                    ],
                }},
            }},
            yaxis: {{ title: 'Count' }},
            yaxis2: {{
                title: 'Status',
                overlaying: 'y',
                side: 'right',
                range: [-0.2, 1.2],
                tickvals: [0, 1],
                ticktext: ['CLOSED', 'OPEN'],
            }},
            hovermode: 'x unified',
        }};

        const config = {{ responsive: true, scrollZoom: true }};

        Plotly.newPlot('graph', traces, layout, config);

        const startInput = document.getElementById('startDate');
        const endInput = document.getElementById('endDate');
        const zoomButton = document.getElementById('zoomButton');
        const resetButton = document.getElementById('resetButton');

        const minDate = new Date(data.timestamps[0]);
        const maxDate = new Date(data.timestamps[data.timestamps.length - 1]);

        function formatInputValue(date) {{
            const offset = date.getTimezoneOffset();
            const local = new Date(date.getTime() - offset * 60000);
            return local.toISOString().slice(0, 16);
        }}

        function applyRange(start, end) {{
            Plotly.relayout('graph', {{
                'xaxis.range': [start, end],
            }});
        }}

        startInput.value = formatInputValue(minDate);
        endInput.value = formatInputValue(maxDate);

        zoomButton.addEventListener('click', () => {{
            const start = new Date(startInput.value);
            const end = new Date(endInput.value);
            if (!start.valueOf() || !end.valueOf() || start >= end) {{
                alert('Please select a valid date range.');
                return;
            }}
            applyRange(start.toISOString(), end.toISOString());
        }});

        resetButton.addEventListener('click', () => {{
            applyRange(minDate.toISOString(), maxDate.toISOString());
            startInput.value = formatInputValue(minDate);
            endInput.value = formatInputValue(maxDate);
        }});
    </script>
</body>
</html>
"""


def parse_total_stands(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        cleaned = value.replace("'", '"')
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"Unable to parse total_stands value: {value}")


def read_csv_file(csv_path):
    rows = []
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if not row:
                continue
            timestamp = (row.get('horodate') or row.get('\ufeffhorodate') or '').strip()
            if not timestamp:
                continue
            station_number = (row.get('number') or '').strip()
            status = (row.get('status') or '').strip().upper()
            total_stands_raw = row.get('total_stands', '')
            parsed = parse_total_stands(total_stands_raw)
            avail = parsed.get('availabilities', {}) if isinstance(parsed, dict) else {}
            rows.append({
                'timestamp': timestamp,
                'station_number': station_number,
                'status': status,
                'capacity': parsed.get('capacity', None) if isinstance(parsed, dict) else None,
                'bikes': avail.get('bikes'),
                'stands': avail.get('stands'),
                'electricalBikes': avail.get('electricalBikes'),
                'mechanicalBikes': avail.get('mechanicalBikes'),
            })
    return rows


def build_graph_data(rows):
    timestamps = []
    capacity = []
    bikes = []
    stands = []
    electrical_bikes = []
    mechanical_bikes = []
    status_values = []
    status_labels = []
    status_colors = []

    for row in rows:
        try:
            dt = datetime.fromisoformat(row['timestamp'])
            timestamps.append(dt.isoformat())
        except ValueError:
            timestamps.append(row['timestamp'])
        capacity.append(row['capacity'] if row['capacity'] is not None else 0)
        bikes.append(row['bikes'] if row['bikes'] is not None else 0)
        stands.append(row['stands'] if row['stands'] is not None else 0)
        electrical_bikes.append(row['electricalBikes'] if row['electricalBikes'] is not None else 0)
        mechanical_bikes.append(row['mechanicalBikes'] if row['mechanicalBikes'] is not None else 0)
        is_open = row['status'] == 'OPEN'
        status_values.append(1 if is_open else 0)
        status_labels.append('OPEN' if is_open else row['status'] or 'UNKNOWN')
        status_colors.append('#2ca02c' if is_open else '#d62728')

    return {
        'timestamps': timestamps,
        'capacity': capacity,
        'bikes': bikes,
        'stands': stands,
        'electricalBikes': electrical_bikes,
        'mechanicalBikes': mechanical_bikes,
        'status_values': status_values,
        'status_labels': status_labels,
        'status_colors': status_colors,
    }


def generate_html(station_number, rows, output_path):
    graph_data = build_graph_data(rows)
    html_content = HTML_TEMPLATE.format(
        station_number=station_number,
        data_json=json.dumps(graph_data),
        status_colors=json.dumps(graph_data['status_colors']),
    )
    Path(output_path).write_text(html_content, encoding='utf-8')
    print(f"Generated HTML page: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate a static HTML graph from a Vélo\'v CSV sample file.')
    parser.add_argument('csv_file', help='Path to the CSV file to load')
    parser.add_argument('-o', '--output', default='station_report.html', help='Output HTML file path')
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows = read_csv_file(csv_path)
    if not rows:
        raise ValueError('No data rows found in CSV file.')

    station_number = rows[0].get('station_number', 'unknown') or 'unknown'
    generate_html(station_number, rows, args.output)


if __name__ == '__main__':
    main()
