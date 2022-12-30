jQuery(document).ready(function($){
	function date_formatting(time) {
      now = new Date(time);
      year = "" + now.getFullYear();
      month = "" + (now.getMonth() + 1); if (month.length == 1) { month = "0" + month; }
      day = "" + now.getDate(); if (day.length == 1) { day = "0" + day; }
      hour = "" + now.getHours(); if (hour.length == 1) { hour = "0" + hour; }
      minute = "" + now.getMinutes(); if (minute.length == 1) { minute = "0" + minute; }
      second = "" + now.getSeconds(); if (second.length == 1) { second = "0" + second; }
      return year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second;
    }

    $('.user-date').each(function(){
        var d = new Date();
        localOffset = d.getTimezoneOffset() / 60 * -1;
        date = Date.parse($(this).html());
        if( !isNaN(date) ){
	        nd = new Date(date + (3600000*localOffset));
	        stringnd = date_formatting(nd);
	        $(this).html(stringnd);
        }
    });


	// *------ fixed navbar START -------*
	var nav = $('.mainmenu');
	
	$(window).scroll(function () {
		if ($(this).scrollTop() > 136) {
			nav.addClass("f-nav");
		} else {
			nav.removeClass("f-nav");
		}
	});
	// *------ fixed navbar END -------*
	
	
	
	
	
	// *------ side menu change color after click START -------*
    var pageName = (location.pathname).split('/').pop();
    if( pageName == '' )
    {
        pageName = 'index.html';
    }

    //$('.branch-menu ul').hide();

    /*$('.branch-menu a').on('click', function()
    {
        //$(this) refers to the clicked element.
        $(this).parents('li').siblings('li').children('ul').hide();
    });*/

    $('.branch-menu').find('a').each(function(index, value)
    {   
        var valuehref = (value.href).split('/').pop();
        
        if(valuehref == pageName)
        {
            // If the pagename matches the href-attribute, then add the 'active' class to the parent li, and show parent ul:s:
            //$(this).addClass('active').parents('ul').show();    
        	$(this).addClass('active');
        	$(this).parent('li').parent('ul').siblings('a').addClass('active');
        }
    });
    // *------ side menu change color after click END -------*
    
    
    
    
    
    // *------- mobile open search bar ------*
    $('.search-open').on('click', function(){
    	var msb = $('.m-search-bar');
    	if(msb.hasClass('hidden')) {
            msb.removeClass('hidden');
        } else {
            msb.addClass('hidden');
        }    
    });
    
});