$(document).ready ->
        $('.betgame-window').hide()
        
        $('.action-button').click ->
                btnid = $(this).attr('id')
                betlist = btnid.split('-')
                bettype = betlist[0]
                game_id = new Number(betlist[1])
                url = $(this).attr('href')
                window.location = url
                
        $('.action-button-testing').click ->
                btnid = $(this).attr('id')
                betlist = btnid.split('-')
                bettype = betlist[0]
                game_id = new Number(betlist[1])
                url = $(this).attr('href')
                eid = '#betgame-window-' + game_id
                $('header > h2').text('loading...')
                form_url = $(eid).attr('href')
                $(eid).load(form_url, {}, () ->
                        $('header > h2').text(form_url)
                        )
                $(eid).show()
                
                
                
        $('#nothere').click ->
                betval = betlist[2]
                betwin_id = "betgame-window-" + game_id
                betwin_id_sel = "#" + betwin_id
                $(betwin_id_sel).text("Bet on this game")
                betwin_visible = $(betwin_id_sel).is(":visible")
                $('header > h2').text(betwin_visible)
                if betwin_visible
                        $(betwin_id_sel).hide()
                else
                        $(betwin_id_sel).show()

                
                         
                
