import argparse
import ast
import csv
import json
import math
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
        const stationNumber = "{station_number}";
        const levels = data.levels;
        const minDate = new Date(levels[levels.length - 1].timestamps[0]);
        const maxDate = new Date(levels[levels.length - 1].timestamps[levels[levels.length - 1].timestamps.length - 1]);
        const startInput = document.getElementById('startDate');
        const endInput = document.getElementById('endDate');
        const zoomButton = document.getElementById('zoomButton');
        const resetButton = document.getElementById('resetButton');
        const graphDiv = document.getElementById('graph');
        let ignoreRelayout = false;

        function formatInputValue(date) {{
            const offset = date.getTimezoneOffset();
            const local = new Date(date.getTime() - offset * 60000);
            return local.toISOString().slice(0, 16);
        }}

        function makeTraces(level) {{
            return [
                {{
                    x: level.timestamps,
                    y: level.capacity,
                    name: 'capacity',
                    mode: 'lines',
                    type: 'scattergl',
                    line: {{ width: 2, color: '#1f77b4' }},
                    hovertemplate: '%{{x}}<br>capacity: %{{y}}<extra></extra>',
                }},
                {{
                    x: level.timestamps,
                    y: level.bikes,
                    name: 'bikes',
                    mode: 'lines',
                    type: 'scattergl',
                    line: {{ width: 2, dash: 'dashdot', color: '#ff7f0e' }},
                    hovertemplate: '%{{x}}<br>bikes: %{{y}}<extra></extra>',
                }},
                {{
                    x: level.timestamps,
                    y: level.stands,
                    name: 'stands',
                    mode: 'lines',
                    type: 'scattergl',
                    line: {{ width: 2, dash: 'dot', color: '#2ca02c' }},
                    hovertemplate: '%{{x}}<br>stands: %{{y}}<extra></extra>',
                }},
                {{
                    x: level.timestamps,
                    y: level.electricalBikes,
                    name: 'electricalBikes',
                    mode: 'lines',
                    type: 'scattergl',
                    line: {{ width: 2, dash: 'dash', color: '#d62728' }},
                    hovertemplate: '%{{x}}<br>electricalBikes: %{{y}}<extra></extra>',
                }},
                {{
                    x: level.timestamps,
                    y: level.mechanicalBikes,
                    name: 'mechanicalBikes',
                    mode: 'lines',
                    type: 'scattergl',
                    line: {{ width: 2, dash: 'longdash', color: '#9467bd' }},
                    hovertemplate: '%{{x}}<br>mechanicalBikes: %{{y}}<extra></extra>',
                }},
                {{
                    x: level.timestamps,
                    y: level.status_values,
                    name: 'status',
                    type: 'bar',
                    marker: {{ color: level.status_colors, line: {{ width: 0 }} }},
                    yaxis: 'y2',
                    customdata: level.status_labels,
                    hovertemplate: '%{{x}}<br>status: %{{customdata}}<extra></extra>',
                    opacity: 0.6,
                }},
            ];
        }}

        function makeLayout(rangeStart, rangeEnd) {{
            return {{
                title: {{ text: 'Station ' + stationNumber, x: 0.01, xanchor: 'left' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.08, xanchor: 'left', x: 0 }},
                margin: {{ t: 90, b: 80, l: 70, r: 70 }},
                xaxis: {{
                    title: 'Date',
                    type: 'date',
                    range: [rangeStart, rangeEnd],
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
                    range: [-0.15, 1.15],
                    tickvals: [0, 1],
                    ticktext: ['CLOSED', 'OPEN'],
                }},
                hovermode: 'x unified',
            }};
        }}

        function bisectLeft(array, value) {{
            let low = 0;
            let high = array.length;
            while (low < high) {{
                const mid = Math.floor((low + high) / 2);
                if (array[mid] < value) {{
                    low = mid + 1;
                }} else {{
                    high = mid;
                }}
            }}
            return low;
        }}

        function chooseLevel(rangeSpan) {{
            const totalSpan = maxDate.getTime() - minDate.getTime();
            const ratio = rangeSpan / totalSpan;
            const thresholds = [0.4, 0.18, 0.08, 0.035, 0.015];
            for (let index = levels.length - 1; index >= 0; index--) {{
                if (ratio <= thresholds[index]) {{
                    return index;
                }}
            }}
            return 0;
        }}

        function sliceLevel(level, startMs, endMs) {{
            const from = bisectLeft(level.timestampsMs, startMs);
            const to = bisectLeft(level.timestampsMs, endMs + 1);
            const slice = {{
                timestamps: level.timestamps.slice(from, to),
                capacity: level.capacity.slice(from, to),
                bikes: level.bikes.slice(from, to),
                stands: level.stands.slice(from, to),
                electricalBikes: level.electricalBikes.slice(from, to),
                mechanicalBikes: level.mechanicalBikes.slice(from, to),
                status_values: level.status_values.slice(from, to),
                status_labels: level.status_labels.slice(from, to),
                status_colors: level.status_colors.slice(from, to),
            }};
            return slice.timestamps.length ? slice : level;
        }}

        function updateChart(startMs, endMs) {{
            const rangeSpan = endMs - startMs;
            const levelIndex = chooseLevel(rangeSpan);
            const level = sliceLevel(levels[levelIndex], startMs, endMs);
            const traces = makeTraces(level);
            const layout = makeLayout(new Date(startMs).toISOString(), new Date(endMs).toISOString());
            ignoreRelayout = true;
            Plotly.react('graph', traces, layout, {{ responsive: true, scrollZoom: true }}).then((gd) => {{
                bindPlotlyEvents(gd);
                ignoreRelayout = false;
            }});
        }}

        function resetView() {{
            startInput.value = formatInputValue(minDate);
            endInput.value = formatInputValue(maxDate);
            updateChart(minDate.getTime(), maxDate.getTime());
        }}

        function relayoutHandler(eventData) {{
            if (ignoreRelayout) {{
                return;
            }}
            const x0 = eventData['xaxis.range[0]'] || eventData['xaxis.range'];
            const x1 = eventData['xaxis.range[1]'];
            if (!x0 || !x1) {{
                return;
            }}
            const start = new Date(x0);
            const end = new Date(x1);
            if (!start.valueOf() || !end.valueOf() || start >= end) {{
                return;
            }}
            startInput.value = formatInputValue(start);
            endInput.value = formatInputValue(end);
            updateChart(start.getTime(), end.getTime());
        }}

        function bindPlotlyEvents(gd) {{
            if (gd && typeof gd.on === 'function' && !gd._relayoutBound) {{
                gd.on('plotly_relayout', relayoutHandler);
                gd._relayoutBound = true;
            }}
        }}

        zoomButton.addEventListener('click', () => {{
            const start = new Date(startInput.value);
            const end = new Date(endInput.value);
            if (!start.valueOf() || !end.valueOf() || start >= end) {{
                alert('Please select a valid date range.');
                return;
            }}
            updateChart(start.getTime(), end.getTime());
        }});

        resetButton.addEventListener('click', resetView);

        startInput.value = formatInputValue(minDate);
        endInput.value = formatInputValue(maxDate);
        updateChart(minDate.getTime(), maxDate.getTime());
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


def safe_int(value):
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0


def read_csv_file(csv_path):
    rows = []
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if not row:
                continue
            timestamp_raw = (row.get('horodate') or row.get('\ufeffhorodate') or '').strip()
            if not timestamp_raw:
                continue
            try:
                dt = datetime.fromisoformat(timestamp_raw)
                timestamp = dt.isoformat()
                timestamp_ms = int(dt.timestamp() * 1000)
            except ValueError:
                timestamp = timestamp_raw
                timestamp_ms = 0
            station_number = (row.get('number') or '').strip()
            status = (row.get('status') or '').strip().upper()
            total_stands_raw = row.get('total_stands', '')
            parsed = parse_total_stands(total_stands_raw)
            avail = parsed.get('availabilities', {}) if isinstance(parsed, dict) else {}
            rows.append({
                'timestamp': timestamp,
                'timestamp_ms': timestamp_ms,
                'station_number': station_number,
                'status': status,
                'capacity': safe_int(parsed.get('capacity') if isinstance(parsed, dict) else 0),
                'bikes': safe_int(avail.get('bikes')),
                'stands': safe_int(avail.get('stands')),
                'electricalBikes': safe_int(avail.get('electricalBikes')),
                'mechanicalBikes': safe_int(avail.get('mechanicalBikes')),
                'status_value': 1 if status == 'OPEN' else 0,
                'status_label': 'OPEN' if status == 'OPEN' else status or 'UNKNOWN',
                'status_color': '#2ca02c' if status == 'OPEN' else '#d62728',
            })
    return rows


def rows_to_level_data(rows):
    return {
        'timestamps': [row['timestamp'] for row in rows],
        'timestampsMs': [row['timestamp_ms'] for row in rows],
        'capacity': [row['capacity'] for row in rows],
        'bikes': [row['bikes'] for row in rows],
        'stands': [row['stands'] for row in rows],
        'electricalBikes': [row['electricalBikes'] for row in rows],
        'mechanicalBikes': [row['mechanicalBikes'] for row in rows],
        'status_values': [row['status_value'] for row in rows],
        'status_labels': [row['status_label'] for row in rows],
        'status_colors': [row['status_color'] for row in rows],
    }


def downsample_rows(rows, max_points):
    total = len(rows)
    if total <= max_points:
        return rows
    window = math.ceil(total / max_points)
    aggregated = []
    for start in range(0, total, window):
        chunk = rows[start:start + window]
        if not chunk:
            continue
        count = len(chunk)
        middle = chunk[count // 2]
        aggregated.append({
            'timestamp': middle['timestamp'],
            'timestamp_ms': middle['timestamp_ms'],
            'capacity': round(sum(row['capacity'] for row in chunk) / count),
            'bikes': round(sum(row['bikes'] for row in chunk) / count),
            'stands': round(sum(row['stands'] for row in chunk) / count),
            'electricalBikes': round(sum(row['electricalBikes'] for row in chunk) / count),
            'mechanicalBikes': round(sum(row['mechanicalBikes'] for row in chunk) / count),
            'status_value': chunk[-1]['status_value'],
            'status_label': chunk[-1]['status_label'],
            'status_color': chunk[-1]['status_color'],
        })
    return aggregated


def make_data_levels(rows, max_points=1500, max_levels=5):
    total = len(rows)
    levels = []
    for level in range(max_levels):
        target = min(total, max_points * (2 ** level))
        if not levels or target > len(levels[-1]['timestamps']):
            level_rows = downsample_rows(rows, target)
            levels.append(rows_to_level_data(level_rows))
        if target >= total:
            break
    return levels


def generate_html(station_number, rows, output_path):
    levels = make_data_levels(rows)
    html_content = HTML_TEMPLATE.format(
        station_number=station_number,
        data_json=json.dumps({'levels': levels}, separators=(',', ':')),
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
