from collections import defaultdict
import time
import datetime
import pandas
import numpy as np
import dateutil
import unicodedata
import re


youtube_link = {
    0: "https://www.youtube.com/watch?v=YWYsHlZ2Utk",
    1: "https://www.youtube.com/watch?v=wZzFE3dyQlU",
    2: "https://www.youtube.com/watch?v=GBd2goR_WLU",
    3: "https://www.youtube.com/watch?v=R0Jbw983eYg",
    4: "https://www.youtube.com/watch?v=57jnkd3reAI",
    5: "https://www.youtube.com/watch?v=I6F_sU1OPrQ",
    6: "https://www.youtube.com/watch?v=Ic6pNxh9cuU",
    7: "https://www.youtube.com/watch?v=k0C7mrbBiy8",
    8: "https://www.youtube.com/watch?v=kZoZKSpWGTI",
    9: "https://www.youtube.com/watch?v=Mdmwu-Ul9Pc",
}

rooms = {
    "stage": "2d-59fTTjJ0",
    "room 1": "WOlN8NwDRmk",
    "room 2": "hYBrHmw4tuU",
    "room 3": "FaMMQK8ub0s",
    "room 4": "DA7vgHrT3OU",
    "room 5": "-hR1FtcGu1A",
    "room 6": "GDV5heQOdUk",
    "room 7": "1gAtVTbcfiQ",
    "room 8": "uifmtaHi_Uo",
    "room 9": "gX3I0xTpLLU",
}
for k, v in rooms.items():
    if k=='stage':
        k = 0
    else:
        k = int(k[5:])
    youtube_link[k] = f'https://www.youtube.com/watch?v={v}'


# From https://github.com/django/django/blob/master/django/utils/text.py
def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def write_abstract(talk, t, track):
    start = dateutil.parser.parse(talk.starttime)
    end = dateutil.parser.parse(talk.endtime)
    talkid = []
    if isinstance(talk.fullname, str):
        talkid.append(slugify(talk.fullname))
    if isinstance(talk.title, str):
        title = '-'.join(slugify(talk.title).split('-')[:5])
        talkid.append(title)
    talkid = 'abstracts/'+'-'.join(talkid)+'.html'
    contents = ''
    if isinstance(talk.title, str):
        contents += f'<h1>{talk.title}</h1>'
    if isinstance(talk.fullname, str):
        contents += f'<h2>{talk.fullname}</h2>'
    if isinstance(talk.coauthors, str):
        contents += f'<h3>{talk.coauthors}</h3>'
    if isinstance(talk.abstract, str):
        abstract = talk.abstract.replace('\n', '<br/>')
        contents += f'<h2>Abstract</h1><p>{abstract}</p>'
    js = r'''
	function LT(t) {
        var m = moment.utc(t).tz(moment.tz.guess());
		document.write(m.format('MMMM Do YYYY, HH:mm z'));
	};
    function time_between(start, end) {
        var s = moment.utc(start);
        var e = moment.utc(end);
        var now = moment();
        return (s<=now) && (now<=e);
    };
    function update_visibility() {
        var now = moment();
        var elems = document.getElementsByClassName("visible_at_time");
        for(var i=0; i<elems.length; i++) {
            s = moment.utc(elems[i].dataset.start);
            e = moment.utc(elems[i].dataset.end);
            if ( (s<=now) && (now<=e) ) {
                elems[i].style.display = "block";
            } else {
                elems[i].style.display = "none";
            }
        }
    };
    setInterval(update_visibility, 60*1000);
    '''
    css = '''
    * {
        font-family: "Trebuchet MS", Helvetica, sans-serif;
    }
    '''
    html = f'''
    <!doctype html>

    <html lang="en">
    <head>
        <meta charset="utf-8">    
        <script type="text/JavaScript" src="https://MomentJS.com/downloads/moment.js"></script>
        <script type="text/JavaScript" src="https://momentjs.com/downloads/moment-timezone-with-data.min.js"></script>
        <title>{talk.title}</title>
        <style>
            {css}
        </style>
        <script type="text/JavaScript">
            {js}
        </script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    </head>
    <body>
        <h3>
            <a href="https://neuromatch.io">Neuromatch</a> 3 /
            <script type="text/JavaScript">LT("{t.strftime('%Y-%m-%d %H:%M')}");</script>
            /
            Track {track}
            /
            {talk.talk_format}
            <div class="visible_at_time" data-start="{start.strftime('%Y-%m-%d %H:%M')}" data-end="{end.strftime('%Y-%m-%d %H:%M')}">
                <a href='{youtube_link[track]}'><i class="fa fa-youtube-play" style="font-size:24px;color:red"></i></a>
                <a href='{youtube_link[track]}'>Watch now on YouTube</a>
            </div>
        </h3>
        {contents}
        <script type="text/JavaScript">
            update_visibility();
        </script>
    </body>
    </html>
    '''
    open(talkid, 'wb').write(html.encode('UTF-8'))
    return talkid


def write_static_html_schedule(filename='submissions-final.csv'):
    talks_df = pandas.read_csv(filename)
    talk_at = defaultdict(list)
    all_times = set()
    for talk in talks_df.iloc:
        if talk.submission_status=="Accepted" and isinstance(talk.track, str):
            if talk.track=="stage":
                track = 0
            else:
                track = int(talk.track[5:])
            # if talk.track[6:]=="":
            #     print(talk.title, talk.fullname)
            # track = int(talk.track[6:])
            #t = dateutil.parser.parse(talk.starttime+' UTC')
            t = dateutil.parser.parse(talk.starttime)
            talk_at[t, track] = talk
            all_times.add(t)
    table_rows = []
    all_times = sorted(list(all_times))
    num_tracks = 1+max(track for t, track in talk_at.keys())
    start_time = datetime.datetime(2020, 10, 26, 13, tzinfo=datetime.timezone.utc)
    end_time = datetime.datetime(2020, 10, 31, 00, tzinfo=datetime.timezone.utc)
    t = start_time
    #_talk_end = dict((str(talk.fullname)+str(talk.title), dateutil.parser.parse(talk.endtime+' UTC')) for talk in talks_df.iloc)
    _talk_end = dict((str(talk.fullname)+str(talk.title), dateutil.parser.parse(talk.endtime)) for talk in talks_df.iloc)
    talk_end = lambda talk: _talk_end[str(talk.fullname)+str(talk.title)]
    def next_time(t):
        dt = t-start_time
        h = dt.total_seconds()//(60*60)
        m = dt.total_seconds()//60-h*60
        firstinhour = m==0
        if m==30:
            idt = datetime.timedelta(seconds=60*30)
            hourchange = True
        else:
            idt = datetime.timedelta(seconds=60*15)
            hourchange = False
        tnext = t+idt
        return tnext, hourchange, firstinhour
    def find_row_span(t, talk):
        # t is current time, set the rowspan to go to the start of the next hour or the end of the talk
        t, hourchange, firstinhour = next_time(t)
        rowspan = 1
        while t<talk_end(talk) and not hourchange:
            rowspan += 1
            t, hourchange, firstinhour = next_time(t)
        return rowspan
    ongoing = {}
    while t<end_time:
        tnext, hourchange, firstinhour = next_time(t)
        talk_at[t].sort(key=lambda x: x[0])
        cell = f'''
        <td class="time">
            <script type="text/JavaScript">LT("{t.strftime('%Y-%m-%d %H:%M')}");</script>
        </td>
        '''
        row = [cell]
        has_contributed = any(talk_at[t, track].talk_format in ('Interactive talk', 'Traditional talk') for track in range(num_tracks) if (t, track) in talk_at)
        spanned_tracks = set()
        for track in range(num_tracks):
            if track in ongoing:
                if t>=talk_end(ongoing[track]):
                    del ongoing[track]
            if (t, track) not in talk_at:
                if track not in ongoing:
                    row.append('<td></td>')
                elif firstinhour: # renew
                    span = f'rowspan="{find_row_span(t, ongoing[track])}"'
                    cell = f'''<td class="talk_cell {ongoing[track].talk_format.replace(' ', '_')}" {span}>... continues ...</td>'''
                    row.append(cell)
            else:
                talk = talk_at[t, track]
                talk_start_time = dateutil.parser.parse(talk.starttime)
                talk_end_time = dateutil.parser.parse(talk.endtime)
                abstract_link = write_abstract(talk, t, track)
                ongoing[track] = talk
                cell = [getattr(talk, v) for v in ['title', 'fullname'] if isinstance(getattr(talk, v), str)]
                cell = [(c.title() if c.upper()==c else c) for c in cell]
                if len(cell)==2 and cell[0]==cell[1]:
                    cell = [cell[0]]
                cell[0] = f'<b>{cell[0]}</b>'
                cell = '<br/>'.join(cell)
                cell = f'<a href="{abstract_link}">{cell}</a>'
                details = []
                details_summary = []
                if isinstance(talk.coauthors, str):
                    details.append(f'<div class="coauthors">{talk.coauthors}</div>')
                    details_summary.append('Coauthors')
                if isinstance(talk.abstract, str):
                    abstract = talk.abstract.replace('\n', '<br/>')
                    details.append(f'<div class="abstract">{abstract}</div>')
                    details_summary.append('Abstract')
                details = '<br/>'.join(details)
                details_summary = ', '.join(details_summary)
                if details:
                    details = f'''
                    <div>&nbsp;</div>
                    <details>
                        <summary>{details_summary}</summary>
                        <div>&nbsp;</div>
                        {details}
                    </details>
                    '''
                if talk.talk_format not in ('Interactive talk', 'Traditional talk'):
                    span = f'rowspan="{find_row_span(t, talk)}"'
                    spanned_tracks.add(track)
                else:
                    span = ''
                cell = f'''
                <td class="talk_cell {talk.talk_format.replace(' ', '_')}" {span}>
                    <i>{talk.talk_format}</i><br/>
                    <div class="visible_at_time" data-start="{talk_start_time.strftime('%Y-%m-%d %H:%M')}" data-end="{talk_end_time.strftime('%Y-%m-%d %H:%M')}">
                        <a href='{youtube_link[track]}'><i class="fa fa-youtube-play" style="font-size: 120%; color:red"></i></a>
                        <a href='{youtube_link[track]}'>Watch now</a>
                    </div>
                    {cell}
                    {details}
                </td>
                '''
                row.append(cell)
        if tnext is None or tnext.hour!=t.hour:
            rowclass = 'rowtime lastinsession'
        else:
            rowclass = 'rowtime'
        row = '\n'.join(row)
        row = f'''
        <script type="text/JavaScript">
            oldday = NewDay(oldday, "{t.strftime('%Y-%m-%d %H:%M')}");
        </script>
        <tr class="{rowclass}" data-start="{t.strftime('%Y-%m-%d %H:%M')}" data-end="{tnext.strftime('%Y-%m-%d %H:%M')}">
            {row}
        </tr>
        '''
        table_rows.append(row)
        t = tnext
    table = '\n'.join(table_rows)
    css = '''
    * {
        font-family: "Trebuchet MS", Helvetica, sans-serif;
    }
    table {
        border-collapse: collapse;
        table-layout: fixed;
    }
    th, td {
        text-align: left;
        padding: 8px;
        vertical-align: top;
    }
    th { background-color: #eeeeee; }
    .talk {
        width: 10em;
    }
    .talk_cell {
        border-left: 1px solid black;
        border-right: 1px solid black;
    }
    tr { border-bottom: 1px dashed #888888; }
    th, .lastinsession, .day { border-bottom: 1px solid black;}
    .day {
        //background-color: #eeccee;
        font-size: 300%;
        font-weight: bold;
    }
    .Interactive_talk { background-color: #f2f2fa; }
    .Traditional_talk { background-color: #f2faf2; }
    .Special_Event { background-color: #ffeeee; }
    .Keynote_Event { background-color: #ffeeff; }
    .coauthors {
        font-size: 80%;
        font-style: italic;
    }
    .abstract {
        font-size: 80%;
    }
    summary {
        font-size: 80%;
    }
    '''
    js = r'''
	function LT(t) {
        var m = moment.utc(t).tz(moment.tz.guess());
		document.write(m.format("LT"));
	}
    function NewDay(old, t) {
        var m = moment.utc(t).tz(moment.tz.guess());
        newday = m.format("dddd MMMM D");
        if(newday!=old) {
            document.write('<tr><td class="day" colspan="COLSPAN">'+newday+'</td></tr>');
        }
        return newday;
    }
    var oldday = "NonsenseValue";
    function openAll() {
        var elems = document.getElementsByTagName("details");
        document.getElementById("btnExpandHideAllDetails").innerHTML = "Hide details";
        document.getElementById("btnExpandHideAllDetails").setAttribute( "onClick", "javascript: closeAll();");

        for (var i = 0; i < elems.length; i++){
            elems[i].setAttribute("open", "true");
        }
    }

    function closeAll() {	
        var elems = document.getElementsByTagName("details");
        document.getElementById("btnExpandHideAllDetails").setAttribute( "onClick", "javascript: openAll();" );
        document.getElementById("btnExpandHideAllDetails").innerHTML = "Expand all details (do this to enable searching abstracts/coauthors in page)";	
        
        for (var i = 0; i < elems.length; i++){
            elems[i].removeAttribute("open");
        }
    }
    function time_between(start, end) {
        var s = moment.utc(start);
        var e = moment.utc(end);
        var now = moment();
        return (s<=now) && (now<=e);
    };
    function update_visibility() {
        var now = moment();
        var elems = document.getElementsByClassName("visible_at_time");
        for(var i=0; i<elems.length; i++) {
            s = moment.utc(elems[i].dataset.start);
            e = moment.utc(elems[i].dataset.end);
            if ( (s<=now) && (now<=e) ) {
                elems[i].style.display = "block";
            } else {
                elems[i].style.display = "none";
            }
        }
    };
    setInterval(update_visibility, 60*1000);    
    function update_row_background() {
        var now = moment();
        var elems = document.getElementsByClassName("rowtime");
        for(var i=0; i<elems.length; i++) {
            s = moment.utc(elems[i].dataset.start);
            e = moment.utc(elems[i].dataset.end);
            if ( (s<=now) && (now<=e) ) {
                elems[i].style.backgroundColor = "#ff8888";
            } else {
                elems[i].style.backgroundColor = "white";
            }
        }
    }
    setInterval(update_row_background, 60*1000);    
    '''.replace("COLSPAN", f'{num_tracks+1}')
    html = f'''
    <!doctype html>

    <html lang="en">
    <head>
        <meta charset="utf-8">    
        <script type="text/JavaScript" src="https://MomentJS.com/downloads/moment.js"></script>
        <script type="text/JavaScript" src="https://momentjs.com/downloads/moment-timezone-with-data.min.js"></script>
        <title>Neuromatch 3.0 provisional schedule</title>
        <style>
            {css}
        </style>
        <script type="text/JavaScript">
            {js}
        </script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    </head>
    <body>
        <h1>Neuromatch 3.0 provisional schedule</h1>
        <p>
            Times are given in the following time zone: 
            <script type="text/JavaScript">
                document.write(moment.tz.guess());
            </script>.
        </p>
        <button id="btnExpandHideAllDetails" onclick="openAll()">Expand all details (do this to enable searching abstracts/coauthors in page)</button>
        <p>&nbsp;</p>
        <table>
            {table}
        </table>
        <script type="text/JavaScript">
            update_visibility();
            update_row_background();
        </script>
    </body>
    </html>
    '''
    open('index.html', 'wb').write(html.encode('UTF-8'))

if __name__=='__main__':
    write_static_html_schedule()
