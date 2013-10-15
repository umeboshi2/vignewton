<div class="main-betgames-view">
  <div class="listview-header">
    <p>NFL Bettable Games</p>
  </div>
  <% from datetime import datetime %>
  <% now = datetime.now() %>
  %for date in dates:
  %if date < now.date():
  <% continue %>
  %endif
  <div class="listview-list">
    <div class="listview-list-entry-header">
      ${date.strftime(game_date_format)}
    </div>
    %for odds in collector.dates[date]:
    %if odds.game.start < now:
      <% continue %>
    %endif
    %if odds.spread == 0 and odds.total == 0:
      <% continue %>
    %endif
    <div class="listview-list-entry">
      <% mkurl = request.route_url %>
      <% game_id = odds.game.id %>
      <% game = odds.game %>
      <% game_url = mkurl('vig_nflgames', context='viewgame', id=game_id) %>
      <% favored_txt = '%s %s' % (odds.favored.city, odds.favored.name) %>
      <% underdog_txt = '%s %s' % (odds.underdog.city, odds.underdog.name) %>
      <% away_txt = '%s %s' % (game.away.city, game.away.name) %>
      <% home_txt = '%s %s' % (game.home.city, game.home.name) %>
      <% summary = odds.game.summary %>
      <% broute = 'vig_betgames' %>
      <% favored_id = 'line-{}-favored'.format(game_id) %>
      <% favored_url = mkurl(broute, context='betfavored', id=game_id) %>
      <% underdog_id = 'line-{}-underdog'.format(game_id) %>
      <% underdog_url = mkurl(broute, context='betunderdog', id=game_id) %>
      <% under_id = 'underover-{}-under'.format(game_id) %>
      <% under_url = mkurl(broute, context='betunder', id=game_id) %>
      <% over_id = 'underover-{}-over'.format(game_id) %>
      <% over_url = mkurl(broute, context='betover', id=game_id) %>
      <% form_url = mkurl('vig_betfrag', context='betover', id='foo') %>
      <a href="${game_url}">${summary}</a><br>
	  <div class="line-table">
            %if odds.spread > 0:
	    <table>
	      <tr class="away-row">
		<td>
		  <a href="${game_url}">${away_txt}</a>
		</td>
		%if odds.favored_id == game.away_id:
		<td>
		  -${odds.spread}
		  %if odds.spread > 0:
                    <input type="button" class="action-button" id="${favored_id}" href="${favored_url}" value="bet">
		  %endif
		</td>
		%else:
		<td>
		  ${odds.spread}
		  %if odds.spread > 0:
		    <input type="button" class="action-button" id="${underdog_id}" href="${underdog_url}" value="bet">
		  %endif
		</td>
		%endif
	      </tr>
	      <tr class="home-row">
		<td>
		  <a href="${game_url}">${home_txt}</a>
		</td>
		%if odds.favored_id == game.home_id:
		<td>
		  -${odds.spread}
		  %if odds.spread > 0:
		    <input type="button" class="action-button" id="${favored_id}" href="${favored_url}" value="bet">
		  %endif
		</td>
		%else:
		<td>
		  ${odds.spread}
		  %if odds.spread > 0:
		    <input type="button" class="action-button" id="${underdog_id}" href="${underdog_url}" value="bet">
		  %endif
		</td>
		%endif
	      </tr>
	    </table>
            %endif
	  </div>
	  <div class="underover-table">
	    %if odds.total > 0:
	    <table>
	      <tr class="over-row">
		<td>
		  over ${odds.total}
		  %if odds.total > 0:
		    <input type="button" class="action-button" id="${over_id}" href="${over_url}" value="bet">
		  %endif
		</td>
	      </tr>
	      <tr class="under-row">
		<td>
		  under ${odds.total}
		  %if odds.total > 0:
		    <input type="button" class="action-button" id="${under_id}" href="${under_url}" value="bet">
		  %endif
		</td>
	      </tr>
	    </table>
	    %endif
	  </div>
    </div>
    <div class="betgame-window" id="betgame-window-${game_id}" href="${form_url}"><div></div></div>
    %endfor
  </div>
  %endfor
</div>

