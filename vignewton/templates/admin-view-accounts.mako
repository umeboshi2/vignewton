<div class="admin-view-accounts-view">
  <% dtformat = '%b %d %Y - %H:%M:%S' %>
  %for acct in accts:
  <div class="listview-header">
    ${acct.name} - $${acct.balance.balance}
  </div>
  %endfor
</div>

