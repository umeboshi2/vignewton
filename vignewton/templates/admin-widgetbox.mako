<div class="base-widgetbox admin-cash-report-view">
  <% accounts.refresh() %>
  <div class="listview-header">
    <p>Cash Report</p>
  </div>
  <div class="listview-list">
    <div class="listview-list-entry-header">
      Main Accounts
    </div>
    <div class="listview-list-entry">
      Cash Balance: ${accounts.cash.balance.balance}<br>
    </div>
    <div class="listview-list-entry">
      Wagers Balance: ${accounts.wagers.balance.balance}<br>
    </div>
    <div class="listview-list-entry">
      Juice Balance: ${accounts.juice.balance.balance}<br>
    </div>
    <div class="listview-list-entry">
      <% acct_bal = accounts.get_account_balance_total()[0] %>
      Total Account Balance: ${acct_bal}<br>
    </div>
    <div class="listview-list-entry">
      Money in System: ${-accounts.inthewild.balance.balance}<br>
    </div>
  </div>
</div>


