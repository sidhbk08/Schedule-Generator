from flask import Flask, render_template, request
from datetime import datetime, timedelta
import random

app = Flask(__name__)

def distribute_durations(total_minutes, num_files, min_dur=1):
    base = total_minutes / num_files
    durations = [base] * num_files
    for _ in range(num_files * 2):
        i, j = random.sample(range(num_files), 2)
        if durations[i] > min_dur:
            delta = min(durations[i] - min_dur, 0.5)
            durations[i] -= delta
            durations[j] += delta
    return durations

def generate_schedule(start_time_str, end_time_str, num_files, breaks):
    start_time = datetime.strptime(start_time_str, "%I:%M %p")
    end_time = datetime.strptime(end_time_str, "%I:%M %p")
    if end_time <= start_time:
        end_time += timedelta(days=1)

    total_minutes = (end_time - start_time).total_seconds() / 60
    total_break_minutes = sum(b[0] for b in breaks)
    work_minutes = total_minutes - total_break_minutes

    if work_minutes <= 0:
        raise ValueError("Total break time exceeds total available time!")
    if work_minutes < num_files * 0.5:
        raise ValueError(f"Not enough time for {num_files} files (need at least 0.5 minutes each).")

    durations = distribute_durations(work_minutes, num_files)
    break_positions = [
        start_time + timedelta(minutes=total_minutes * 0.25),
        start_time + timedelta(minutes=total_minutes * 0.75),
    ]

    schedule = []
    current_time = start_time
    break_idx = 0

    for dur in durations:
        label_suffix = ""
        while break_idx < len(breaks) and current_time >= break_positions[break_idx]:
            b_len, _ = breaks[break_idx]
            label_suffix = f" + Break ({b_len} mins)"
            current_time += timedelta(minutes=b_len)
            break_idx += 1

        f_start = current_time
        f_end = f_start + timedelta(minutes=dur)
        schedule.append({
            'start': f_start.strftime('%I:%M:%S %p'),
            'end': f_end.strftime('%I:%M:%S %p'),
            'label': f"Work{label_suffix}"
        })
        current_time = f_end

    return schedule

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            start_time = request.form['start_time']
            end_time = request.form['end_time']
            num_files = int(request.form['num_files'])
            b1 = int(request.form['break1'])
            b2 = int(request.form['break2'])

            breaks = [(b1, f'Break ({b1} mins)'), (b2, f'Break ({b2} mins)')]
            schedule = generate_schedule(start_time, end_time, num_files, breaks)

            return render_template('result.html', schedule=schedule)

        except Exception as e:
            return f"<h3>Error: {str(e)}</h3>"

    return render_template('form.html')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)