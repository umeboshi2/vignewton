<div id="data-area">
  <% evurl = request.route_url('maincal_json', context='view', id='events') %>
  <input id="event-source-url" type="hidden" value="${evurl}" />
</div>
<div id="loading">
  <h2>Loading Events</h2>
</div>
<div id="maincalendar">
</div>
