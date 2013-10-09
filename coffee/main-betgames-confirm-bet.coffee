$(document).ready ->
        $('#confirm-bet-button').click ->
                url = $('#confirm-url').val()
                window.location = url
                
        $('#cancel-bet-button').click ->
                url = $('#cancel-url').val()
                window.location = url
