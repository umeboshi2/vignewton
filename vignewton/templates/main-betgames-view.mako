<div class="main-betgames-view">
  <div class="listview-header">
    <p>NFL Bettable Games</p>
  </div>
  %for date in dates:
  <div class="listview-list">
    <div class="listview-list-entry-header">
      ${date.strftime(game_date_format)}
    </div>
    %for odds in collector.dates[date]:
    <div class="listview-list-entry">
      <% mkurl = request.route_url %>
      <% game_id = odds.game.id %>
      <% game_url = mkurl('vig_nflgames', context='viewgame', id=game_id) %>
      <% favored_txt = '%s %s' % (odds.favored.city, odds.favored.name) %>
      <% underdog_txt = '%s %s' % (odds.underdog.city, odds.underdog.name) %>
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
      <div class="action-button" id="${favored_id}" href="${favored_url}">${favored_txt}</div>
      over 
      <div class="action-button" id="${underdog_id}" href="${underdog_url}">${underdog_txt}</div>
      by ${odds.spread} totalling
      <div class="action-button" id="${under_id}" href="${under_url}">under</div>
      ${odds.total}
      <div class="action-button" id="${over_id}" href="${over_url}">over</div><br>
    </div>
    <div class="betgame-window" id="betgame-window-${game_id}" href="${form_url}"><div></div></div>
    %endfor
  </div>
  %endfor
</div>

