/* Consts */
let noEffects = false;


/* Helper Functions */
function toggleLoadingCircle(on=false, displayCSS='', containerSelector='.content_container', imageSelector='.loading_circle'){
    if (noEffects === true){return false;}
    if (containerSelector != '' && imageSelector != ''){
        if ($(imageSelector).length && $(containerSelector).length) {
            /* start gif from begning */
            $(imageSelector).attr('src', $(imageSelector).attr('src'));
            if (on === true){
                $(containerSelector).hide();
                $(imageSelector).show();
               
            } else {
                $(imageSelector).hide('fast');
                $(containerSelector).show('fast');
            }
            return on;
        }
    }
    console.log('toggleLoadingCircle: Unable to find content container or loading image elements.');
}

function displayAjaxError(message, status='success'){
    $("#ajax_flashes").html('');
    if (message==null){
      // clear messages
      return false;
    }
    if ($("#ajax_flashes").length){
        $("#ajax_flashes").append(`
          <div class="alert alert-${status} alert-dismissible fade show">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <span> ${message}</span>
          </div>
        `);
    }
}
// get formated datetime acording to py and db rules 
function getFullDate(type='date'){
  let date = '';
  try {
    const getOneFromTwo = (condition, val1, val2)=>{
        return condition ? val1 : val2;
    };
    const now = new Date();
    const month = getOneFromTwo((parseInt(now.getMonth()) >= 9), (now.getMonth()+1), `0${(now.getMonth()+1)}`);
    const day = getOneFromTwo(parseInt(now.getDate()) > 9, now.getDate(), `0${now.getDate()}`);

    if (type === 'datetime'){
        hours = getOneFromTwo((now.getHours() > 9), now.getHours(), `0${now.getHours()}`);
        minutes = getOneFromTwo((now.getMinutes() > 9), now.getMinutes(), `0${now.getMinutes()}`);
        seconds = getOneFromTwo((now.getSeconds() > 9), now.getSeconds(), `0${now.getSeconds()}`);
        date = `${now.getFullYear()}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } else {
        date = `${now.getFullYear()}-${month}-${day}`;
    }
    
  } catch (error){
      console.log('error from getFullDate', error);
  }

  return date.trim();
}

/* hover effect */
function applyHoverEffect(){
    if (noEffects === true){return false;}
    $(document).on({
        mouseenter: function (e) {
            $(this).addClass('shadow-lg');
            
        },
        mouseleave: function (e) {
            $(this).removeClass('shadow-lg');
        }
    }, ".hover_shadow");
    return true;
}

/* get formated date 2024-01-011 */
function getFullDate(){
  let date = '';
  try {
    const now = new Date();
    const month = (parseInt(now.getMonth()) >= 9) ? (now.getMonth()+1) : `0${(now.getMonth()+1)}`;
    const day = (parseInt(now.getDate()) >= 10) ? now.getDate() : `0${now.getDate()}`;
    date = `${now.getFullYear()}-${month}-${day}`;
  } catch (error){
      console.log('error from getFullDate', error);
  }

  return date;
}

/* !function uses data-supplier attribute and value of search input to display element using data-selector *= contains global js function fast and use DOM selector only for search (simple used for direct given cell only with no column select) like data-attr = x */
function SearchByJS(
    itemsSelector='.suppliers', searchTarget='#search_supplier', dataSearchAttr='data-search-supplier', searchConidition='*=',cb=(callback)=>{}
    ){
    const searchSupplier = function (){
      if (!$(searchTarget).length){return false;}
      if ($(searchTarget).val()){
              const targetSupplierName = String($(searchTarget).val()).trim();
              /* Search Using DOM selector ~= *= = */
              const matchedSuppliers = $(`[${dataSearchAttr}${searchConidition}"${targetSupplierName}"]`);
              if ($(matchedSuppliers).length){
                  $(itemsSelector).hide();
                  $(matchedSuppliers).show('fast');
              } else {
                  $(itemsSelector).show('fast');
              }
      } else {
              $(itemsSelector).show('fast');
      }
    };
    return cb(searchSupplier);
}

const postData = async(url = '', data = {}) => {
	const response = await fetch(url, {
		method: 'POST',
		credentials: 'same-origin',
		headers: {
			'Content-Type': 'application/json',
		},
		// Body data type must match "Content-Type" header
		body: JSON.stringify(data),
	});
	try {
		const newData = await response.json();
		return newData;
	} catch (error) {
		console.log("error", error);
	}
}


/* (searchComponent) simple full jquery/html dom function that can complete search for any number of database columns 
eg:99m and html cards search done using DOM so it speed after setup like DOM selector (no css required and work with bs4 and not remove elements or styles)
*/
/* this addon used to enable calling this function multiple times to handle the selectors */
function searchComponent(speed='slow',easing='swing', cp=function(){return true;}, addon='', condition='=', rowBuildCB=()=>{}, table='', parent_id=0){
    const stopSearchForm = function(){
        if ($(`form#search_form${addon}`).length){
            $(`form#search_form${addon}`).on('submit', (ev)=>{
              ev.preventDefault();
              return false;
            });
        }
    };

    
    if (noEffects === true){
        console.log('Can not start search component please ask admin to turn on noEffects');
        /* stop search form if any */
        stopSearchForm();
        return false;
    }
    
    /* Full JQuery component */
    const dataSearchAttrs = {};
    let searchColumnsIndex = 0;
    let selectType = 'current';    
    if ($("body").length && $(`form#search_form${addon}`).length && $(`#cancel_search${addon}[type='button']`).length && $(`#search_value${addon}`).length &&
    $(`#search_by${addon} option.search_column${addon}`).length && typeof(cp) == 'function'){
      
      $(`#cancel_search${addon}`).hide();      


      /*get dynamic data-search attributes and options value for column name*/
      $(`#search_by${addon} option.search_column${addon}`).each( (_i, dataSearchAttr)=>{
          const columnName = $(dataSearchAttr).val().trim();
          if (columnName){
            dataSearchAttrs[columnName] = `data-search-${columnName}`;
            searchColumnsIndex += 1;
          }
      });


  
      /* check if nesesery add submit event or no search columns found*/
      if (searchColumnsIndex < 1){
        console.log('Stoped Search components no valid search options columns found');
        return false;
      }
  
      /* add class css to overide bs, and added to card after hide effect completed in callback */
      $("body").append(`<style>.hidden_search_card${addon}{ display: none !important; }</style>`);
      
      
      /* function to remove hidden cards with same effect and callback */
      function cancelSearch(speed, easing, cp){
        /* remove search card added from searver (the best async is to keep current spreate over server to keep function smooth and every part work alone as sperate component with not relation in cdoe) */
        $(`.search_all_card${addon}`).remove();
        /* this for jquery works with bs4 becuase added css class with display:none !important so remove it and start make jquery effect that will run even if bs display element as it slow eg can not after display use: $(oldHidden).hide();*/
        const oldHidden = $(`.hidden_search_card${addon}`);
        $(`.hidden_search_card${addon}`).removeClass(`hidden_search_card${addon}`);
        /* to apply the user provided cb after complete last action for example display alert or empty cells etc */
        $(oldHidden).each( (hi, elm)=>{
          if (hi+1 == $(oldHidden).length){
            $(elm).show(speed, easing, cp);
          } else {
            $(elm).show(speed, easing);            
          }
        });
        
      }
      /*
        return Array.from([].filter.call(elements, function(element){
          return RegExp(searchVal, 'i').test(element.getAttribute(dataAttrName));
        }));
      */
      // get insesntive search list, by loop over elements instead of it was using query selector, no insesntive operator in js selector *= only
      function getQueryInsensitiveList(searchTerm, dataAttrName){
        searchTerm = searchTerm.toLowerCase();
        let result = [];
        // this is only search line
        $(`.searching_card${addon}[${dataAttrName}]`).each( (i, item)=>{
            const stringLower = $(item).attr(dataAttrName).toLowerCase();
            if ((stringLower.includes(searchTerm))){
                result.push(item);
            }
        });
        return result;
      }

      /* event listener for search (all hide actions) */
      $(`form#search_form${addon}`).on('submit', async (event)=>{
        event.preventDefault();
        /* to allow reaserch not pass cp (clean and old search which hide cards, before start new search) */
        cancelSearch(speed, easing, ()=>{});
        selectType = ($(`select#search_type${addon}`).length) ? $(`select#search_type${addon}`).val() : 'current';
        const searchValue = $(`#search_value${addon}`).val().trim();
        const searchColumn = $(`#search_by${addon}`).val().trim();
        const dataAttrName = dataSearchAttrs[searchColumn];
        console.log(dataAttrName);  
        
        //dataAttrName && searchValue && selectType == 'current'
        if (dataAttrName && selectType == 'current'){
          /* html selector search condition set (stoping this way targetCards to make Insensitive search as no selector js for insesntive *= easy add i*= == 'your insestive search add new operator string sure there are insesntive core c++ std::regex pattern(".*a.*", std::regex_constants::icase);' */
          //const targetCards = $(`.searching_card${addon}[${dataAttrName}${condition}'${searchValue}']`);
          //const targetCardsArr = $(targetCards).toArray();
          const targetCardsArr = getQueryInsensitiveList(searchValue, dataAttrName);
          console.log(targetCardsArr)
          $(`.searching_card${addon}`).each( (s, searchingCard)=>{
            if ( !targetCardsArr.includes($(searchingCard)[0])){
              /* this is how hide any bs4 (d-flex, row) with jquery effect css + callback*/
              $(searchingCard).hide(speed, easing, ()=>{
                $(searchingCard).addClass(`hidden_search_card${addon}`);
                /* call usercb */
                if (s+1 == $(`.searching_card${addon}`).length){
                  cp();                  
                }
              });
            }
          });
          $(`#cancel_search${addon}`).show();
          
        } else if (searchColumn && selectType == 'all' && typeof(rowBuildCB) === 'function') {
          //searchColumn && searchValue && selectType == 'all' && typeof(rowBuildCB) === 'function'          
          const searchResponse = await postData('/search', {column: searchColumn, value: searchValue, table: table, parent_id: parent_id});

          // hide current page or previous cards (targetCardsArr will be data from server in this scope) (must be done here after await as incase multiple clicks on button if clear before await it may clear all data for the 3 clicks while first await not completed yet thats why it will keep concate the rows or repeat rows, but now after await when data come from server clear any previous data and start display so no matter 9999 clicks in same time each time will wait response hide the previous and start display new, instead of hide previous and await for response) other solution if need keep hide before await hide button of search and display it after search but this more logical
          $(`.searching_card${addon}`).each( (s, searchingCard)=>{
              /* this is how hide any bs4 (d-flex, row) with jquery effect css + callback in clearn search before server start set speed to 1 as it addiotonal clean*/
              $(searchingCard).hide(1, easing, ()=>{
                $(searchingCard).addClass(`hidden_search_card${addon}`);
                /* call usercb */
                if (s+1 == $(`.searching_card${addon}`).length){
                  cp();                  
                }
              });
          });
          if (searchResponse && searchResponse.code == 200 && Array.isArray(searchResponse.data)){
            const serverData = searchResponse.data;
            const targetTableBody = $(`#table_display${addon} tbody`);
            if ($(targetTableBody).length){
              serverData.forEach( (ServerDataObj)=>{
                // rowBuildCB return empty string if invali row in it
                const newRowHTML = rowBuildCB(ServerDataObj);
                if (newRowHTML){
                  $(targetTableBody).append(newRowHTML);
                }
              });
            }

          } else if (searchResponse && searchResponse.code != 200 && searchResponse.message) {
            displayAjaxError(searchResponse.message, 'danger');
          } else {
            console.log(searchResponse);
            displayAjaxError("unable to search server right now", 'danger');
          }

          $(`#cancel_search${addon}`).show();
          // send search data and get result using ajax
          //alert("hello server search feature"+searchColumn+searchValue);
        } else {
          cancelSearch(speed, easing, cp);
          $(`#cancel_search${addon}`).hide();
        }
      });

      /* cancel search event */
      $(`#cancel_search${addon}`).on('click', ()=>{
        cancelSearch(speed, easing, cp);
        $(`#cancel_search${addon}`).hide();
        $(`#search_value${addon}`).val('');
        /* this normal event fired when cancel search happend, usefull for integerate search with diffrent components, like multiple select */
        $(window).trigger('searchComponent.cancelSearch');        
      });

      /* cancel search and remove search server card when siwtch to search current page */

      return true;
    }
  
    /* if there were a form but no have inputs or not valid for any reason preventdefault submision as it js form*/
    stopSearchForm();
    console.log('unable to start search component');
    return false;
  }


/* function to dynamic fill wtform for delete any model using it's id and set dynamic url for form aswell (can used in any page) */
function deleteWtformsModalProccess(dataAttId, formId, idInputId, modalId) {

    function onDeleteBtnClick(event){
      if ($(event.currentTarget).length) {
        const formAction = String($(event.currentTarget).attr('data-url')).trim();
        const dashboardId = String($(event.currentTarget).attr(dataAttId)).trim();
        if ($(`#${formId}`).length && $(`#${formId} input#${idInputId}`).length && formAction && dashboardId) {
            /* set target id and action url of delete model */
            $(`#${formId} input#${idInputId}`).val(dashboardId);
            $(`#${formId}`).attr('action', formAction);
        }
      }
    }

    $(".wtform_modal_deletebtn").on('click', onDeleteBtnClick);

    $(`#${modalId}`).on('hidden.bs.modal', () => {
        if ($(`#${formId}`).length) {
            $(`#${formId}`).attr('action', '');
        }
        if ($(`#${formId} input#${idInputId}`).length) {
            $(`#${formId} input#${idInputId}`).val('');
        }
    });

    return onDeleteBtnClick;
}

/* function to toggle settings menu */
function toggleSettingsToast(){
  $(document).ready(function(){
    if ($("#open_settings").length){
      $("#open_settings").click(function(event){
        
        if ($(event.currentTarget)){
          if (!$(event.currentTarget).attr('data-status') || $(event.currentTarget).attr('data-status') == 'closed'){
            $("#settings_toast").css('display','');
            $(event.currentTarget).attr('data-status', 'open');            
            $('.toast').toast('show');
          } else {            
            $(event.currentTarget).attr('data-status', 'closed');            
            $('.toast').toast('hide');
            $("#settings_toast").css('display','none');
          }
          return true;
        }
      });

      /* event optional for toggle display for lists */
      if ($("#switch_display").length){
        $("#switch_display").on('change', switchListDisplay);
      }

    } else {
      console.log("unable to start toggleSettingsToast no settings button");
    }
  });
}
/* function to switch display bettween table and card */
function switchListDisplay(event){
  if ($(event.currentTarget).length && $("#card_display").length && $("#table_display").length){
    if ($(event.currentTarget).val() == 'table'){
      $("#card_display").hide('mid', 'swing', ()=>{
        $("#table_display").show('mid');
      });
    } else {
      $("#table_display").hide('mid', 'swing', ()=>{
        $("#card_display").show('mid');
      });
    }
    return true;
  } else {
    console.log('unable to apply switch display becuase missing required elements');
    return false;
  }
}

function updateClientColorMode(event){
  if ($(event.currentTarget).length){
    if ($(event.currentTarget).val() == 'dark'){

    } else {

    }
    return true;
  }
}

/* (new Pagination way) (let user browse all buttons exist with js) function get a list of pagantion's urls from server pagantion function , and get the value of page query paramter, it dynamic create paganted group of buttons to displayed, 1- Add better UX as it allow for user fast select any page for example from page 1 go to page 40, 2- less server request than normal pagantion eg freelancer > it requires at least (40/5) requests to see the group of buttons contains page 40, here you can browse all buttons exist and it just url in array so to reach unlimited page x you need only 1 request to server, and displaying the buttons done with js. 3-count of all rows must set in freelancer to display valid buttons so same start at least performance backend in speed as getting the button only needed count of rows */
function displayPaginationComponent(paginationBtns, paginationPage, containerIDs, paginationGroupI = -1) {

  const btnIndex = paginationPage - 1;
  const pagBtnsLimit = 5;
  const totalPagBtnsGroups = Math.ceil(paginationBtns.length / pagBtnsLimit);
  const paginationRanges = [];
  let currentBtnGroupI = 0;
  let currentBtnsGroup = [];
  let currentBtnsGroupIndexes = [];

  let isLastPage = false;
  let lastPage = [];
  let isFirstPage = false;
  let firstPage = [];

  
  for (let r = 0; r < totalPagBtnsGroups; r++) {
      paginationRanges.push([r * pagBtnsLimit, (r + 1) * pagBtnsLimit]);
  }

  
  


  if (paginationGroupI === -1) {

      for (let pr = 0; pr < paginationRanges.length; pr++) {
          const currentRangeList = paginationRanges[pr];
          if ((btnIndex >= currentRangeList[0]) && (btnIndex < currentRangeList[1])) {
          

              /*get sliced group of target buttons based on index of button */
              currentBtnsGroup = paginationBtns.slice(currentRangeList[0], currentRangeList[1]);
              currentBtnGroupI = pr;
              /* this way make sure currentBtnsGroup.length equal always to currentBtnsGroupIndexes.lenght*/
              for (let i = 0; i < currentBtnsGroup.length; i++) {
                  const currentBtnPageI = i + (currentRangeList[0] + 1);
                  currentBtnsGroupIndexes.push(currentBtnPageI);
              }
          }
      }
  } else {

      /*Direct set data to specfic group this called from click on previous or next buttons*/

      if (paginationGroupI < paginationRanges.length) {
          
          const currentRangeList = paginationRanges[paginationGroupI];
          currentBtnsGroup = paginationBtns.slice(currentRangeList[0], currentRangeList[1]);
          currentBtnGroupI = paginationGroupI;
          for (let i = 0; i < currentBtnsGroup.length; i++) {
              const currentBtnPageI = i + (currentRangeList[0] + 1);
              currentBtnsGroupIndexes.push(currentBtnPageI);
          }

      }
  }

  // 3 cases of last, if only 1 page, if in last group, if in loaded first time in last group eg: loaded on page 9 and 9 in last group 
  if ( paginationRanges.length-1 == currentBtnGroupI ){
    isLastPage = true;
  }

  if (currentBtnGroupI == 0){
    isFirstPage = true;
  }

  // handle last page
  if (isLastPage === false && paginationBtns.length > 0){
    lastPage = [String(paginationBtns.length), paginationBtns[paginationBtns.length-1]];
  }


  // handle first page
  if (isFirstPage === false && paginationBtns.length > 0){
    firstPage = [1, paginationBtns[0]];
  }

  let pagantionHTML = '<ul class="pagination">';

  let previousClasses = (currentBtnGroupI == 0) ? 'previous page-item disabled' : 'previous page-item';
  let previousPaginationGroupI = (currentBtnGroupI > 0) ? currentBtnGroupI - 1 : 0;
  pagantionHTML += `<li class="${previousClasses}"><button type="button" class="page-link">Previous</button></li>`;
  // handle add first page button
  if (firstPage.length == 2){    
    pagantionHTML += `<li class="page-item"><a class="page-link" href="${firstPage[1]}">${firstPage[0]}</a></li>`;
    pagantionHTML += `<li class="page-item"><a class="page-link" href="javascript:void(0)">...</a></li>`;
  }

  currentBtnsGroup.forEach((BtnUrl, btnUrlIndex) => {
      const btnPageIndex = currentBtnsGroupIndexes[btnUrlIndex];
      let btnClasses = 'page-item';
      if (paginationPage == btnPageIndex) {
          btnClasses += ' active';
      }

      pagantionHTML += `<li class="${btnClasses}"><a class="page-link" href="${BtnUrl}">${btnPageIndex}</a></li>`;

  });

  /* index of btn group is last group in ranges or there are next group */
  let nextClasses = (currentBtnGroupI < (paginationRanges.length - 1)) ? 'next page-item' : 'next page-item disabled';
  let nextPaginationGroupI = (currentBtnGroupI < (paginationRanges.length - 1)) ? currentBtnGroupI + 1 : paginationRanges.length - 1;


  // handle add last page button
  if (lastPage.length == 2){
    pagantionHTML += `<li class="page-item"><a class="page-link" href="javascript:void(0)">...</a></li>`;
    pagantionHTML += `<li class="page-item"><a class="page-link" href="${lastPage[1]}">${lastPage[0]}</a></li>`;
  }

  pagantionHTML += `<li class="${nextClasses}"><button type="button" class="page-link">Next</button></li>`;
  pagantionHTML += '</ul>';

  /* containerIDs is list for better performance set the same pagantion in more than container without recall the function for newId (used in top and bottom pagantion for same list) */
  containerIDs.forEach((containerID)=>{
    const currentContainer = document.querySelector(`#${containerID}`);
    if (currentContainer){
      currentContainer.innerHTML = pagantionHTML;
      const previousBtn = document.querySelector(`#${containerID} .previous`);
      const nextBtn = document.querySelector(`#${containerID} .next`);
  
      previousBtn.addEventListener("click", () => {
        const paginationBtnsVar = paginationBtns;
        const paginationPageVar = paginationPage;
        const containerIDsVar = containerIDs;
  
        displayPaginationComponent(paginationBtnsVar, paginationPageVar, containerIDsVar, previousPaginationGroupI);
  
      });
  
  
      nextBtn.addEventListener("click", () => {
          const paginationBtnsVar = paginationBtns;
          const paginationPageVar = paginationPage;
          const containerIDsVar = containerIDs;
  
          displayPaginationComponent(paginationBtnsVar, paginationPageVar, containerIDsVar, nextPaginationGroupI);
      });
    } else {
      console.log(`Element With iD:${containerID} not found`);
    }


    


  });

}

/* get the redirect_url query parameter and update the form action_redirect input */
function setFormRedirectByUrl(customRedirect=null){
  let redirect_url = '';
  if ($("#action_redirect").length){
    if (customRedirect == null){
      const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
      });
      console.log(params.redirect_url)
      if (params.redirect_url){
        redirect_url = params.redirect_url;
        $("#action_redirect").val(params.redirect_url);
      }
    } else {
      $("#action_redirect").val(customRedirect);
    }
  }
  if ($("#cancel_link").length && redirect_url){
    $("#cancel_link").attr('href', redirect_url);
  }
  
}


/* fill edit platform form with data */
function fillEditPlatForm(){
  $(".edit_platform").on('click', (event)=>{
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-platform-id') && $("#name_edit").length && $("#platform_id_edit").length && $(`#edit_platform_form`).length && $(event.currentTarget).attr('data-url') && $(event.currentTarget).attr('data-platform-name')) {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const platform_id = String($(event.currentTarget).attr('data-platform-id')).trim();
        const platform_name = String($(event.currentTarget).attr('data-platform-name')).trim();      
        $("#platform_id_edit").val(platform_id);
        $("#name_edit").val(platform_name);
        $(`#edit_platform_form`).attr('action', action_url);
    }
  });

  $('#editPlatformModal').on('hidden.bs.modal', () => {
    if ($("#platform_id_edit").length){
      $("#platform_id_edit").val("");
    }
    if ($("#name_edit").length){
      $("#name_edit").val("");
    }
    if ($('#edit_platform_form').length){
      $('#edit_platform_form').attr('action', '');
    }
  });
}


function fillEditLocation(){
  $(".edit_location").on('click', (event)=>{
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-location-id') && $("#location_name_edit").length && $("#location_id_edit").length && $(`#edit_location_form`).length && $(event.currentTarget).attr('data-url') && $(event.currentTarget).attr('data-location-name')) {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const location_id = String($(event.currentTarget).attr('data-location-id')).trim();
        const location_name = String($(event.currentTarget).attr('data-location-name')).trim();      
        $("#location_id_edit").val(location_id);
        $("#location_name_edit").val(location_name);
        $(`#edit_location_form`).attr('action', action_url);
    }
  });

  $(`#editLocationModal`).on('hidden.bs.modal', () => {
    if ($("#location_id_edit").length){
      $("#location_id_edit").val("");
    }
    if ($("#location_name_edit").length){
      $("#location_name_edit").val("");
    }

    if ($('#edit_location_form').length){
      $('#edit_location_form').attr('action', '');
    }
    
  });
}


function fillEditBin(){
  $(".edit_bin").on('click', (event)=>{
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-bin-id') && $("#bin_name_edit").length && $("#bin_id_edit").length && $(`#edit_bin_form`).length && $(event.currentTarget).attr('data-url') && $(event.currentTarget).attr('data-bin-name')) {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const bin_id = String($(event.currentTarget).attr('data-bin-id')).trim();
        const bin_name = String($(event.currentTarget).attr('data-bin-name')).trim();      
        $("#bin_id_edit").val(bin_id);
        $("#bin_name_edit").val(bin_name);
        $(`#edit_bin_form`).attr('action', action_url);
    }
  });

  $(`#editBinModal`).on('hidden.bs.modal', () => {
    if ($("#bin_id_edit").length){
      $("#bin_id_edit").val("");
    }
    if ($("#bin_name_edit").length){
      $("#bin_name_edit").val("");
    }

    if ($('#edit_bin_form').length){
      $('#edit_bin_form').attr('action', '');
    }
  });
}

function fillEditCategory(){
  $(".edit_category").on('click', (event)=>{
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-category-id') && $("#category_id_edit").length && $("#code_edit").length && $("#label_edit").length && $("#level_edit").length && $("#parent_code_edit").length && $('#edit_category_form').length && $(event.currentTarget).attr('data-url') && typeof($(event.currentTarget).attr('data-category-code')) !== 'undefined' && typeof($(event.currentTarget).attr('data-category-label')) !== 'undefined' && typeof($(event.currentTarget).attr('data-category-level')) !== 'undefined' && typeof($(event.currentTarget).attr('data-category-parent_code')) !== 'undefined') {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const category_id = String($(event.currentTarget).attr('data-category-id')).trim();
        const category_code = String($(event.currentTarget).attr('data-category-code')).trim();
        const category_label = String($(event.currentTarget).attr('data-category-label')).trim();
        const category_level = String($(event.currentTarget).attr('data-category-level')).trim();
        const category_parent_code = String($(event.currentTarget).attr('data-category-parent_code')).trim();
        $("#category_id_edit").val(category_id);
        $("#code_edit").val(category_code);
        $("#label_edit").val(category_label);
        $("#level_edit").val(category_level);
        $("#parent_code_edit").val(category_parent_code);
        $(`#edit_category_form`).attr('action', action_url);
    }
  });

  $('#editCategoryModal').on('hidden.bs.modal', () => {
    if ($("#category_id_edit").length){
      $("#category_id_edit").val("");
    }
    if ($("#code_edit").length){
      $("#code_edit").val("");
    }
    if ($("#label_edit").length){
      $("#label_edit").val("");
    }
    if ($("#level_edit").length){
      $("#level_edit").val("");
    }
    if ($("#parent_code_edit").length){
      $("#parent_code_edit").val("");
    }

    if ($('#edit_category_form').length){
      $('#edit_category_form').attr('action', '');
    }
  });
}


function fillEditForm(triggerSelector='', formSelector='', modalSelector='', dataAttrs={}, inputIds={}, customTypes={}){
  // check run one time only when page loaded
  if (
    typeof(dataAttrs) === 'object' && typeof(inputIds) === 'object' && 
    typeof(customTypes) === 'object',
    Object.keys(dataAttrs).length === Object.keys(inputIds).length &&
    formSelector && $(formSelector).length && 
    modalSelector && $(modalSelector).length &&
    triggerSelector
    ){
      
      
    // dynamic check make sure each prop on (dataAttr which main will used props) from exist on input id (this will end function setup on page will not add the event also and this loop run one time only on first load page)
    for (let prop in dataAttrs){
      if (!inputIds.hasOwnProperty(prop) || !String(dataAttrs[prop]).trim() || !String(inputIds[prop]).trim() || !$(inputIds[prop]).length){
        console.log(`${prop} is invalid or not exist arugment`);
        return false;
      }
    }


    $(triggerSelector).on('click', (event)=>{

      if ($(event.currentTarget).length && $(event.currentTarget).attr('data-url')){
        // dynamic check exsting of data-attr and it's input
        for (let prop in dataAttrs){
          if (typeof $(event.currentTarget).attr(dataAttrs[prop]) === 'undefined' || $(event.currentTarget).attr(dataAttrs[prop]) === false){
            console.log(`Must define all provide dataAttr on target elm, undefined: ${prop} -> ${dataAttrs[prop]}`);
            return false;
          }
        }
        // start clear the actions
        for (let prop in dataAttrs){
          //console.log($(event.currentTarget).attr(dataAttrs[prop]).trim());
          
          //console.log($(inputIds[prop]));
          // handle special types of inputs
          const setVal = $(event.currentTarget).attr(dataAttrs[prop]).trim();
          const inputToFilled = $(inputIds[prop]);
          if (customTypes.hasOwnProperty(prop) && customTypes[prop].hasOwnProperty('open') &&
              typeof(customTypes[prop]['open']) === 'function') {
            // (handle all custom elements 1 check small pc usages) check first if input in custom types have set custom type methods valid function can dynamic set any element exist or new element will added in future 99% logical, even can make ajax action to display value with jinja2 data
            customTypes[prop]['open'](setVal, inputToFilled);
          } else {
            inputToFilled.val(setVal);
          }
        }

        
        $(formSelector).attr('action', $(event.currentTarget).attr('data-url'));
      } else {
        console.log("can not get target or missing data-url");
      }
    });
  
    $(modalSelector).on('hidden.bs.modal', () => {
      for (let prop in dataAttrs){
          if (customTypes.hasOwnProperty(prop) && customTypes[prop].hasOwnProperty('close') && typeof(customTypes[prop]['close']) === 'function') {
            customTypes[prop]['close']($(inputIds[prop]));
          } else {
            $(inputIds[prop]).val('');
          }
      }
      $(formSelector).attr('action', '');
    });
  } else {
    console.log("fillEditForm not started length of data attributes must be equal to length of input that will updated");
  }
}

/* integerted with search throw 1 event cancel search, and visible elements (searchComponent use display none for process search result) */
function multipleSelectComponent(checkboxSelector='', dataLabel='', actionModals=[], selectAllSelector='', openModalCB=null, closeModalCB=null){
  let checkedCheckBoxes = [];
  let selectedValues = [];
  let selectedLabels = [];
  // true means can start select all
  let selectAllStatus = true;
  const publicFunction = {};

  /* validate actions modals objects (to make function dyanmic focus only with select provid array of objects for each action modal eg:delete_catalogue, update_catalogue_catagory, or any other action provided) */
  let allActionsReady = (Array.isArray(actionModals) && actionModals.length > 0) ? true : false;
  for (let a=0; a<actionModals.length; a++){
   let actionModal = actionModals[a];
   if (!(
     actionModal.modalId && actionModal.startActionBtn && 
     $(actionModal.modalId).length && $(actionModal.startActionBtn).length
     )){        
     allActionsReady = false;
     break;
   }
  }

  
  
  /* Start function check if all arugments valid */
  if (allActionsReady && checkboxSelector && $(checkboxSelector).length){

   /* incase of submit any form rest selected inputs for browser back button and searchComponent (note search component uses form to make search, so this will also integert with other components like searchComponent, and fix the browser back button too to clear checked inputs when action form or other forms submited) */ 
   $('form').on('submit', function(e){

     oldSelected = $(`${checkboxSelector}:checked:visible`);
     $(checkboxSelector).prop('checked', false);
     $(checkboxSelector).trigger('change');

   });

   /* easy integerate (inhirte) multipleSelectComponent with searchComponent (no need changes in one or both functions)  */
   $(window).on('searchComponent.cancelSearch', function(){
    $(checkboxSelector).prop('checked', false);
    $(checkboxSelector).trigger('change');
   });

   function onChangeCheckBoxSelectAll(e){
      checkedCheckBoxes = Array.from($(`${checkboxSelector}:checked:visible`)).filter( (elm)=>{
        /* must provide items labels for next action */
        if ($(elm).length && $(elm).attr('value') && $(elm).val() && $(elm).attr(dataLabel)){
          return $(elm);
        }
      });

      selectedValues = checkedCheckBoxes.map((checkBox)=>{
          return $(checkBox).val();
      });

      selectedLabels = checkedCheckBoxes.map( (checkBox)=>{
        return $(checkBox).attr(dataLabel);
      });

      if (checkedCheckBoxes.length > 0){
        // if one or more than one item checked display all actions buttons
        actionModals.forEach( (actionModal)=>{
          $(actionModal.startActionBtn).show('fast');
        });
      } else {
        actionModals.forEach( (actionModal)=>{
          $(actionModal.startActionBtn).hide('fast');
        });
      }

      if (selectAllSelector && $(selectAllSelector).length){
         /* always work with visible elements only to easy integerate with search */
        if ($(`${checkboxSelector}:visible`).length == checkedCheckBoxes.length){
          // total visible elements same as total visible elements checked
          selectAllStatus = false;
          $(selectAllSelector).text('Unselect All');
        } else {
          selectAllStatus = true;
          $(selectAllSelector).text('Select All');
        }
      }
   }
   
   $(checkboxSelector).on('change', onChangeCheckBoxSelectAll);
   publicFunction['onChangeCheckBoxSelectAll'] = onChangeCheckBoxSelectAll;

   actionModals.forEach( (actionModal)=>{
       $(actionModal.modalId).on('shown.bs.modal', function(e) {
         
       if ((actionModal.setFormIdsInputVal === true || typeof(actionModal.setFormIdsInputVal) === 'undefined') && actionModal.formInputSelector && $(actionModal.formInputSelector).length){
         /* set action form input value (this way it will never need do action for input value when modal closes even if modal opened with empty selected) */
         $(actionModal.formInputSelector).val(selectedValues.join(","));
       }
 
       // display total element text if provided
       if (actionModal.totalElement && $(actionModal.totalElement).length){
         $(actionModal.totalElement).text(selectedValues.length);
       }

       if ((actionModal.displayLabels === true || typeof(actionModal.displayLabels) === 'undefined') && actionModal.actionLabesSelctor && $(actionModal.actionLabesSelctor).length){
          $(actionModal.actionLabesSelctor).html("");

          // display labels if displayLabels set in current modal data setup obj
          let actionLabesHtml = '';
          selectedLabels.forEach( (labelText)=>{
            actionLabesHtml += `<span class="badge badge-secondary mr-1 mt-1">${labelText}</span>`;
          });
          $(actionModal.actionLabesSelctor).html(actionLabesHtml);
       }

       // call openModalCB if exist (SelectComponent working around 2 main lists selectedValues, selectedLabels) any cb must use this 2 arugments
       if (typeof(actionModal.openModalCB) === 'function'){
          actionModal.openModalCB(selectedValues, selectedLabels);
       }
     });
     
     actionModals.forEach( (actionModal)=>{
       $(actionModal.modalId).on('hide.bs.modal', function(e) {

         if ((actionModal.displayLabels === true || typeof(actionModal.displayLabels) === 'undefined') && actionModal.actionLabesSelctor && $(actionModal.actionLabesSelctor).length){
           // empty labels
           $(actionModal.actionLabesSelctor).html("");
         }
         // empty total elements text if exist
         if (actionModal.totalElement && $(actionModal.totalElement).length){
           $(actionModal.totalElement).text("0");
         }
         // if selectAll exist reset it
         
         // if there are callback for close modal call it
         if (typeof(actionModal.closeModalCB) === 'function'){
            actionModal.closeModalCB();
         }
       });
     });

   });




   /* Make Toggle Select All btn only by check input and trigger change event */
   if (selectAllSelector && $(selectAllSelector).length){
     $(selectAllSelector).on('click', function(){
       if (selectAllStatus){
         $(checkboxSelector).prop('checked', true);
         $(checkboxSelector).trigger('change');
         $(selectAllSelector).text('Unselect All');
         selectAllStatus = false;
       } else {
         $(checkboxSelector).prop('checked', false);
         $(checkboxSelector).trigger('change');
         $(selectAllSelector).text('Select All');
         selectAllStatus = true;
       }
     });
   }
   return publicFunction;
  } else {
   console.log('multipleSelectComponent not started');
  }
}



// this component asynced with flask so it not require any code in flask endpoints so it final result tretet as normal request to page with query limit paramter
function limitPerPageComponent(){
  if ($("#limit_select").length && $("#custom_limit_cont").length && $("#custom_limit_option").length && $("#custom_limit_input").length && $("#set_custom_btn").length && $("#limit_select").attr('data-save-limit')){
    
    const maxLimit = 1000;
    let previousLimit = null;

    // function prevent editing form html and broke functionality always return valid number bigger than 0 and less than max for server request length variables also private protected no access outside
    const limitOr10 = (l)=>{      
      let limit = String(l).trim();
      // parseInt will handle float
      return ((limit && !(isNaN(limit)) && limit <= maxLimit && limit > 0) === true) ? parseInt(limit) : 10;
    }

    async function setLimitAJAX(limit){
      let success = true;
      try {
        const res = await fetch($("#limit_select").attr('data-save-limit'), {
          method: 'POST',
          credentials: "same-origin",
          headers:{
            "Content-Type": "application/json"
          },
          body: JSON.stringify({limit}),
        });
        const data = await res.json();
        console.log(data);
        if (!data || data.code != 200){
          success = false;
        }
      } catch (error){
        console.warn('error while sending ajax request, no intenert connection maybe', error);
        success = false;
      }
      return success;
    }

    async function onLimitChange(e){     

      if ($(e.currentTarget).length){
        
        if ($(e.currentTarget).val()){
          // direct change page limit (casted only if selected value not custom)

          // ! if you need switch from custom to the inital value also cast reload remove this (safe) only removed if limitOptionExit removed, if limitOptionExit removed not need remove this, if removed this remove previousLimit
          // for better UX if user selected value before and switch to custom to test and back to the previous selected value not reload page (ux only not effect values or types) use only if to set previous as page reload after new value valid assigned
          if (previousLimit && previousLimit == $(e.currentTarget).val()){
            $("#custom_limit_cont").css('display', 'none');
            return false;
          }

          // hide custom
          $("#custom_limit_cont").css('display', 'none');
          $("#limit_select").prop('disabled', true);
          $("#limit_select").removeAttr('title');

          // set number of limit using ajax to session (note incase any invalid number gotten return default 10) !! for secuirty reason if user tried edit html I will not inform him there are error and set the value to 10 as default
          const selectedLimit = limitOr10($(e.currentTarget).val());
          const setLimitData = await setLimitAJAX(selectedLimit);
          reloadOrDisplayError(setLimitData);
        } else {
          // custom set page limit (display)
          $("#custom_limit_cont").css('display', 'block');
        }

      } else {
        displayAjaxError('Unable to update limit per page right now, due to system issue please report this problem.', 'danger');
        console.log('invalid target can not run onLimitChange');
      }
    }

    async function handleCustom(){

      const selectedLimit = parseInt(String($("#custom_limit_input").val()).trim());
      // make sure user enter valid limit number (component controlled by maxLimit private variable (private means can not accessed or edited from console))
      if (isNaN(selectedLimit) || selectedLimit <= 0 || selectedLimit > maxLimit){
        displayAjaxError(`Invalid custom limit, please enter number bigger than 0 and less than or equal to ${maxLimit}.`, 'warning');
        return false;
      }


      // (can remove me safe to repeat action if same custom selected) small performance feature and ux, Avoids not needed ajax call, and page reload, incase user selected same custom limit number, use prop to change the custom option to the exist custom option, and trigger change event so onLimitChange will called and automatic detect this is previous selected as it do dynamiclly and hide the container (this makes sure logic work dynamic when option changed even if it custom created the app handle it, and logic work in circle)
      const limitOptionExit = $(`#limit_select option[value='${selectedLimit}']`);
      if (limitOptionExit.length){
        limitOptionExit.prop('selected', true).trigger('change');
        return false;
      }

      $("#limit_select").prop('disabled', true);
      $("#custom_limit_cont").css('display', 'none');
      const setLimitData = await setLimitAJAX(selectedLimit);
      reloadOrDisplayError(setLimitData, onFailureCB=()=>{$("#custom_limit_cont").css('display', 'block');});
    }

    // This final function is called after ajax for both hard and custom limit, reloading the page or displaying an error message if it fails
    function reloadOrDisplayError(ajaxSuccess, onFailureCB=null){

      if (ajaxSuccess){
          // successfull saved limit and update the number, here page will reloaded
          location.reload();
      } else {
          // unable to save limit
          displayAjaxError('Unable to update limit per page right now, please check your internet connection and try again', 'danger');
          console.warn('error while saving limit with ajax');
          $("#limit_select").prop('disabled', false);

          // additonal actions when ajax fails, only used in custom for UX best ux, 
          if (typeof(onFailureCB) === 'function'){
            onFailureCB();
          }
      }

    }

    function setLimitOptionOnLoad(){
      // set limit when load
      const sessionLimit = parseInt(String($("#limit_select").attr('data-limit')).trim());
      // dynamic set max of input based on variable value (only when user uses up and down button)
      $("#custom_limit_input").prop('max', maxLimit);
      $("#custom_limit_input").attr('title', `Max Value is ${maxLimit}`);
      
      // invalid limit provided or session limit not setted yet stop load handle
      if (isNaN(sessionLimit) || sessionLimit <= 0 || sessionLimit > maxLimit){
        return false;
      }
      
      const limitOption = $(`#limit_select option[value='${sessionLimit}']`);
      console.log(limitOption.length, sessionLimit);
      if (limitOption.length > 0){
        // this handle both, if option is static html, or custom option with same value of static option, eg: user selected custom and enter 100
        limitOption.eq(0).prop('selected', true);
      } else {
        //custom limit setted before as function very strict any other number is custom as it follow rules of limit > 0 and < 1000 max (unkown html option)
        console.log(`iam the remaning not cast if value is exist already in static options like 100, ${sessionLimit}`);
        $("#custom_limit_option").before(`<option value="${sessionLimit}">${sessionLimit}</option>`);
        const newOpt = $(`#limit_select option[value='${sessionLimit}']`);
        if (newOpt.length){
          newOpt.prop('selected', true);
        } else {
          // this must not happend but incase elm not added detect that and not set the previousLimit as value not selected
          console.warn('Error, can not create new jquery elm');
          return false;
        }
      }

      // save previous value when page loaded
      previousLimit = sessionLimit;

      $("#limit_select").attr('title', `selected is ${previousLimit} items per page`);
    }

    // dynamic set value of saved selected limit using js
    setLimitOptionOnLoad();

    $("#limit_select").on('change', onLimitChange);
    $("#set_custom_btn").on('click', handleCustom);


    return true;
  } else {
    console.warn('unable to start limitPerPageComponent mising required element');
    return false;
  }
}


/* shadow component that apply order by table headers for any table in the page with class arrangable (it work separately without effect any events that's why it like shadow can used in any app ) also note this able to add the sort to more than one table in same page */
function orderByColumnsComponent() {
  const orderOrignal = {};
  let orderedBefore = false;
  // function used to return sorted DOM array 
  const sorter = (domArr = [], index=0, asc = true) => {
      // note domArr is jquery object not Array it have slice, sort but not have reverse so convert jquery Object to array then after complete convert array back to jquery object
      const copyArr = Array.from(domArr).slice();
      copyArr.sort((a, b) => {
          const aTD = $(a).find('td').eq(index);
          const bTD = $(b).find('td').eq(index);
          // make sure given index are vaild else throw exception and stop all remaning sort process
          if (aTD.length && bTD.length){
            const aString = $(aTD).text().trim();
            const bString = $(bTD).text().trim();

            /* small dynamic check without write data attrs (as string diffrent from numbers when sort if both a and b are float (float accept both integers and float) so convert to integers) */
            const floatA = parseFloat(aString);
            const floatB = parseFloat(bString);
            if (!isNaN(floatA) && !isNaN(floatB)) {
              return (floatA < floatB) ? -1 : (floatA > floatB) ? 1 : 0;
            } else {
              return (aString < bString) ? -1 : (aString > bString) ? 1 : 0;
            }
          } else {
            throw 'Sort could not sort invaild index.';
          }
      });
      return (asc == true) ? $(copyArr) : $(copyArr.reverse());
  };
  
  
  // function to apply the shadow sort that not effect events other way would .html('') (newArr must be jquery object)
  const orderHTMLByArr = (newArr, targetTable) => {
      let previousElm = null;
      $(newArr).each((_i, currentElm) => {
          if (previousElm) {
              // here there are previous elm so insert after this previous elm
              $(currentElm).insertAfter(previousElm);
              previousElm = $(currentElm);
          } else {
              const firstElm = $(targetTable).find('tbody tr:first-of-type');
              if (firstElm.length) {
                  // here this is first elm of order so insert before any elm
                  $(currentElm).insertBefore(firstElm);
                  previousElm = $(currentElm);
              }
          }
      });
  };

  // this function called every time before any order action to make sure order done by one column only and back all things to default (it only back the target table not all tables)
  const backToOriginal = (theTable, tableId) => {
      $(theTable).find("th").attr('data-state', 'none');
      // remove any old class
      const arrowClasses = ['fa-arrow-up', 'fa-arrow-down', 'fa-arrow-right'];
      arrowClasses.forEach((classToRemove) => {
          $(theTable).find('th i.arrange_state').removeClass(classToRemove);
      });
      $(theTable).find('th i.arrange_state').addClass('fa-arrow-right');
  
      // (runs only if table ordered before for performance) to avoid order by two columns and not contain the function and give unknown result back the rows to default order before any new order (incase one column only clicked this not show effect and may more performance but incase user clicked multiple columns this will do the target final result the order method knows exatly what returned result not random)
      if (orderedBefore && orderOrignal.hasOwnProperty(tableId)) {
          console.log("I called");
          orderHTMLByArr(orderOrignal[tableId], theTable);
      }
  };
  
  // event listener function that handle the order based on target table only so it not effect any other tables use that component
  const orderColumns = (e) => {
      if ($(e.currentTarget).length) {
          const dataState = $(e.currentTarget).attr('data-state');
          const stateIcon = $(e.currentTarget).find('i.arrange_state').eq(0);
          const targetTable = $(e.currentTarget).closest("table.arrangable");
          const tableId = targetTable.attr("id");
          const indexOfColumn = $(e.currentTarget).index();
          // for performance incase no rows not make any actions
          const tableRows = $(targetTable).find('tbody tr');
  
          if (dataState && stateIcon.length && tableRows.length && targetTable.length && tableId) {

              // take backup one time from table 
              if (!orderOrignal.hasOwnProperty(tableId)) {
                  orderOrignal[tableId] = Array.from(targetTable.find('tbody tr'));
              }
  
              console.log(dataState, stateIcon[0], targetTable[0], tableId);
  
              
              // start order
              if (dataState == 'none') {
                  backToOriginal(targetTable, tableId);
                  // order asc
                  $(targetTable).find('th')
                  $(e.currentTarget).attr('data-state', 'asc');
                  stateIcon.addClass('fa-arrow-up');

                  const sortedDomArr = sorter(tableRows, indexOfColumn, true);
                  // apply shadow order
                  orderHTMLByArr(sortedDomArr, targetTable);
                  console.log(sortedDomArr, sortedDomArr[0], sortedDomArr[1]);
                  // back data to original incase no other orders (Complex)
              } else if (dataState == 'asc') {
                  backToOriginal(targetTable, tableId);
                  // order desc
                  $(e.currentTarget).attr('data-state', 'desc');
                  stateIcon.addClass('fa-arrow-down');
                  const sortedDomArr = sorter(tableRows, indexOfColumn, false);
                  orderHTMLByArr(sortedDomArr, targetTable);
                  console.log(sortedDomArr, sortedDomArr[0], sortedDomArr[1]);
              } else {
                  // back to default
                  backToOriginal(targetTable, tableId);
              }
              orderedBefore = true;
  
          }
      }
  };
  
  // setup the component requirments
  $('.arrangable').each((i, arrangeTable) => {
  
      // handle dynamic ignore indexes of tables
      const dataIgnore = $(arrangeTable).attr('data-ignore');
      let headersToIgnore = [];
      if (dataIgnore) {
          headersToIgnore = dataIgnore.split(',').map((itemNum) => {
              let item = parseInt(itemNum);
              if (!isNaN(item)) {
                  return item;
              } else {
                  return false;
              }
          }).filter((mappedItem) => {
              return mappedItem !== false;
          });
      }
  
  
      const tableHeaders = $(arrangeTable).find("th");
      tableHeaders.each((h, tableHeader) => {
          if (!headersToIgnore.includes(h)) {
              $(tableHeader).append(`<i class="fa fa-arrow-right font_13px arrange_state"></i>`);
              $(tableHeader).attr('data-state', 'none');
              $(tableHeader).addClass('cursor-pointer');
              tableHeader.addEventListener('click', orderColumns);
          }
      });
  });

}

// simple function to move group of buttons based on user screen view eg if large screen and this is form if user on bottom of page put buttons at bottom else at top
function toggleContentUpDown(contentSelector='', upSelector='', downSelector=''){
  if (contentSelector && $(contentSelector).length && upSelector && $(upSelector).length && downSelector && $(downSelector).length){
     $(window).scroll( ()=>{
       if ($(window).scrollTop() != 0 && $(window).scrollTop() + $(window).height() >= ($(document).height() - 100)){
           // down
            $(downSelector).append($(contentSelector));
        } else {
           // default up (also in smallest screen default which no scroll default is up)
           $(upSelector).append($(contentSelector));
       }
    });
  }
}

function generateBarcodeActions(elmSelector='', dataSelector='', maxLength=48){
  if (elmSelector && $(elmSelector).length && dataSelector && $(dataSelector).length){

    const targetSelect = $(elmSelector);
    const getSelectedVals = ()=>{
      const values = [];
      const selectedValues = targetSelect.val();
      if (selectedValues){
        for (let k=0; k<selectedValues.length; k++){
          const currentLength = values.toLocaleString().replaceAll(',','').length;
          if (currentLength >= maxLength){
            break;
          }
          const colkey = selectedValues[k];
          const dataColVal = targetSelect.attr(`data-${colkey}`);
          if (typeof(dataColVal) !== undefined && dataColVal !== false){
            // values to get commas
            if ((currentLength + dataColVal.length + (values.length-1)) < maxLength){
              values.push(dataColVal);
            } else {
              continue;
            }
          }
        }
        selectedValues.forEach((colkey)=>{

        });
      }
      return values;
    };

    $(elmSelector).on('change', ()=>{
      
      const values = getSelectedVals(targetSelect);
      console.log(values);
      $(dataSelector).val(values.join(','));
       /*
      const dataColVal = target.attr(`data-${target.val()}`);
     
      if (dataColVal){
        alert(dataColVal);
      }*/
    });
  }
}

function setKeyTemp(key='', val='', rewrite=true, remove=false){
  let success = false;
  try {      
  
    if (remove){
      // remove localstorage var if exist
      if (getKeyTemp(key) !== null){
          localStorage.removeItem(key);
          success = null;
      }
    } else if (rewrite){
      // Set Item, update exsting item
      localStorage.setItem(key, val);
      success = true;
    } else {
      // set only if not exist
      if (getKeyTemp(key) === null){
          localStorage.setItem(key, val);
          success = true;
      }
    }
  } catch (e) {
    console.log("setKeyTemp error", e);
    success = false;
  }
  return success;
}

function getKeyTemp(key){
  let keyTemp = null;
  try {
    // Set Item
    keyTemp = localStorage.getItem(key);      
    //document.getElementById("demo").innerHTML = localStorage.getItem("lastname");
  } catch (e) {
    console.log("getKeyTemp error", e);
  }
  return keyTemp;
}

function getQueryParm(queryParm){
  let value = null;
  try {
    const urlParams = new URLSearchParams(window.location.search);
    value = urlParams.get(queryParm);
  } catch (error){
    console.log('error can not get query param', error);
  }
  return value;
}


function bbLocalSaverComponent(key='bbk', checkboxSelector='#importOrdersModal #orders_key_saver', valueSelector="#importOrdersModal #api_key"){
  // that secuirty client side technique all variables methods not accessed from console
  if ((checkboxSelector && $(checkboxSelector).length) && (valueSelector && $(valueSelector).length)){
    
    const effect = function(time=100, repeat=3, cp=function(){}){
      let timeout = null;
      let effectIndex = 0;

      if (repeat > 0){
        function repeater(callback=cp){
            if (timeout){
              clearTimeout(timeout);
            }
            effectIndex += 1;
            if (effectIndex > 0 && effectIndex <= repeat){
              callback();
              timeout = setTimeout(repeater,time);
            } else {
              return false;
            }
        }
      }
      repeater();
    }

    let save = true;
    let effectClean = null;
    const toggleSave = function(){
      let status = false;
      if ((checkboxSelector && $(checkboxSelector).length) && (valueSelector && $(valueSelector).length)){
        if ($(checkboxSelector).is(':checked')){
          // only work with not empty value
          if ($(valueSelector).val()){
              // set key and value
              if (save){
                status = setKeyTemp(key, $(valueSelector).val());            
              } else {
                // for performance not write the variable if already set in begning  page script runs from
                status = setKeyTemp(key, $(valueSelector).val(), false);
                save = true;
              }
          } else {
            $(checkboxSelector).prop('checked', false);

            // here this DC repeater for any effect method, 1- time in milisecond, 2- count of loops, 3- DC callback function repeated (usally use cb the start and clean after it for DC technqiue) 
            effect(200, 2, ()=>{
                if (effectClean){
                  clearTimeout(effectClean);
                }
                if ($(valueSelector).length){
                  $(valueSelector).addClass("alert_timeout");
                }
                effectClean = setTimeout(()=>{
                  if ($(valueSelector).length){
                    $(valueSelector).removeClass("alert_timeout");
                  }
                }, 100);
            });
          }

        } else {
          // clear old saved
          status = setKeyTemp(key, null, null, remove=true);
        }
      }
      console.log(status);
    };

    $(checkboxSelector).on('change', toggleSave);

    $(valueSelector).on('change', function(){
      // not trigger the change event to not call toggleSave
      $(checkboxSelector).prop('checked', false);
      $(checkboxSelector).trigger("change");
    });

    // when this script first runs check status first
    if (getKeyTemp(key) !== null){
      save = false;
      $(valueSelector).val(getKeyTemp(key));
      $(checkboxSelector).prop('checked', true);
      $(checkboxSelector).trigger("change");
    }

  } else {
    console.warn('localStorageSaver not started missing required elements.');
  }
}

function longTimeFormComponent(formSelc="", mainSelc="", loadingSelc="", modalSelector=""){
  if ((formSelc && $(formSelc).length) && (mainSelc && $(mainSelc).length) && (loadingSelc && $(loadingSelc).length)){
    $(formSelc).eq(0).on("submit", function(e){
      
      // option close modal if provided
      if (modalSelector && $(modalSelector).length){
        $(modalSelector).eq(0).modal('hide');
      }

      $(mainSelc).eq(0).hide('fast');
      $(loadingSelc).eq(0).show('fast');
    });
  } else {
    console.log("longTimeFormComponent error");
  }
}

// toggle between multiple components 
function siwtchComponent(e=null, link_elm=null, data_target=null){
  if ((e === null && data_target && link_elm) || (e && $(e.currentTarget).length && $(e.currentTarget).attr('data-target') && $($(e.currentTarget).attr('data-target')).length)){
    const dataTarget = (e === null && data_target) ? data_target : $(e.currentTarget).attr('data-target');
    const linkElm = (e === null && link_elm) ? $(link_elm) : $(e.currentTarget);
    const newActive = $(dataTarget);
    const newLink = linkElm;

    $(".switch_components").hide();
    $(".active_component").removeClass('active_component');
    newActive.show('fast', null, ()=>{
              newLink.addClass("active_component");
    });
  } else {
    console.log('siwtchComponent not worked');
  }
}

// delete some rows component
function deleteSomeRowsComponent(contSelector = '', modalId = '', formSelector = '', actionContSelector = '', someInputsSelector = '', reprsContSelector = '', actionPrefex = '', append = true, actionClasses = '', actionBtnClasses='', actionTxt = '') {
  // global scobed within component variables (private variables as well no accsed or able use)
  const actionConts = contSelector && $(contSelector).length ? $(contSelector) : null;
  const modalElm = modalId && $(modalId).length ? $(modalId) : null;
  const formInput = formSelector && $(formSelector).length ? $(formSelector) : null;
  const actionContElm = actionContSelector && $(actionContSelector).length ? $(actionContSelector) : null;
  const deleteSomeInput = someInputsSelector && $(someInputsSelector).length ? $(someInputsSelector) : null;
  const reprsCont = reprsContSelector && $(reprsContSelector).length ? $(reprsContSelector) : null;
  
  // notification and prevent no check again and message for make sure function ready
  if (!actionConts || !modalElm || !formInput || !actionContElm || !deleteSomeInput) {
          const requireds = {
                  actionConts,
                  modalElm,
                  formInput,
                  actionContElm,
                  deleteSomeInput
          };
          for (prop in requireds) {
                  if (!requireds[prop]) {
                          console.log(`Missing ${prop}`);
                  }
          }
          return false;
  }
  // one time insert new create checkbox
  const actionSelector = `elms_${actionPrefex}`;
  const actionBtnId = `delete_sum_${actionPrefex}`;
  const labelSelector = `delete_label_${actionPrefex}`;
  const toggleSelectAllId = `toggle_all_${actionPrefex}`;
  const deleteAllTxt = 'Delete All';
  let formAction = '';
  if ($(actionContElm).attr('data-action')){
    formAction = $(actionContElm).attr('data-action');
  } else {
    console.log("data-action attr is required");
    return false;
  }
  
  $(actionContElm).append(`
    <button type="button" id="${actionBtnId}" class="btn btn-danger btn-sm" data-toggle="modal" data-target="${modalId}" style="display:none;">Delete Selected</button>
    <button type="button" id="${toggleSelectAllId}" class="btn btn-secondary btn-sm ${actionBtnClasses}">${deleteAllTxt}</button>
    `);
  // insert checkbox inputs data-repr
  for (let ContI = 0; ContI < $(actionConts).length; ContI++) {
          const actionCont = actionConts[ContI];
          if ($(actionCont).attr("data-id")) {
                  const titleAttr = actionTxt ? `title="${actionTxt}"` : '';
                  const reprUsed = $(actionCont).attr("data-repr") ? `data-repr="${$(actionCont).attr("data-repr")}"` : '';
                  const deleteRowId = $(actionCont).attr("data-id");
                  const elmTxt = `
          <label class="form-check-label ${actionClasses} ${labelSelector}" ${titleAttr}>
            <input type="checkbox" class="form-check-input ${actionSelector}" value="${deleteRowId}" ${reprUsed} />
          </label>`;
                  if (append) {
                          $(actionCont).append(elmTxt);
                  } else {
                          $(actionCont).prepend(elmTxt);
                  }
          } else {
                  $(`.${labelSelector}`).remove();
                  console.log(`Found elm not have data-id required attr at index ${ContI}`);
                  return false;
          }
  }
  const boxesClass = `.${actionSelector}`;
  $(boxesClass).on("change", () => {
          if ($(`${boxesClass}:checkbox:checked`).length) {
                  if ($(`#${actionBtnId}`).is(":hidden")) {
                          // some times already previous element checked so no need show
                          $(`#${actionBtnId}`).show('fast');
                          $(`#${toggleSelectAllId}`).attr("data-select", "true");
                          $(`#${toggleSelectAllId}`).text("Undo Select");
                  }
          } else {
                  // only hide will done when last element selected and done 1time
                  $(`#${actionBtnId}`).hide('fast');
                  
                  $(`#${toggleSelectAllId}`).removeAttr("data-select");
                  $(`#${toggleSelectAllId}`).text(deleteAllTxt);
          }
  });
  
  if (!$(`#${toggleSelectAllId}`).length || !$(`#${actionBtnId}`).length){
    console.log("delete all or delete select buttons not created");
    return false;
  }
  
  const clickDeleteSelected = ()=>{
    const checkedIds = Array.from($(`${boxesClass}:checkbox:checked`)).map((elm)=>{return $(elm).val() && String($(elm).val()).trim() ? $(elm).val() : false;});
    // return only false found
    const invalidIds = checkedIds.filter((elmVal)=>{ return !elmVal; });


    if (invalidIds.length > 0){
      console.log("invalid ids or empty are found");
      return false;
    }
    if (!$(formInput).length && !$(deleteSomeInput).length){
      console.log("Missing required elements formInput, deleteSomeInput");
      return false;
    }

    
    $(formInput).attr('action', formAction);
    $(deleteSomeInput).val(checkedIds.join(','));
    
    // display optional items will deleted
    if (reprsCont && $(reprsCont).length){
       // optional repr on any not on all even (return any true found)
       const reprsElmsTxt = Array.from($(`${boxesClass}:checkbox:checked[data-repr]`)).map((elm)=>{return $(elm).attr('data-repr') && String($(elm).attr('data-repr')).trim() ? `<div class="m-0">${$(elm).attr('data-repr')}</div>` : false;}).filter((elmVal)=>{ return elmVal; }).join('');
       if (reprsElmsTxt){
          $(reprsCont).html(reprsElmsTxt);
       }
    }
    
    return true;
  };
  // select all checkbox toggle
  $(`#${toggleSelectAllId}`).on("click", ()=>{
 
    if ($(`#${toggleSelectAllId}`).attr("data-select")){
      // unselect
      $(`#${toggleSelectAllId}`).removeAttr("data-select");
      $(`${boxesClass}:checkbox`).prop("checked", false);
      $(`#${toggleSelectAllId}`).text(deleteAllTxt);
      $(`#${actionBtnId}`).hide('fast');
    } else {
      // select
      $(`#${toggleSelectAllId}`).attr("data-select", "true");
      $(`${boxesClass}:checkbox`).prop("checked", true);
      $(`#${toggleSelectAllId}`).text("Undo Select");
      // alot benfit and also required not only for performance unlike trigger but for make sure open after all checked not first trigger
      clickDeleteSelected();
      $(modalElm).modal('show');
    }
  });
  
  // on click before show modal excuted one time
  $(`#${actionBtnId}`).on("click", clickDeleteSelected);

  // on modal close excuted on time (not the cb)
  $(modalElm).on('hide.bs.modal', function(e) {
    $(formInput).attr('action', '');
    $(deleteSomeInput).val('');
    $(reprsCont).html('');
  });
}


function actionPositionYSwitcher(scrollerS = "", moverS = "", topContS = "", botContS = "", modalSelc="") {
  if (scrollerS && moverS && topContS && botContS && modalSelc && $(scrollerS).length && $(moverS).length && $(topContS).length && $(botContS).length && $(modalSelc).length) {
      // avoid duplicate event listener
      const scroll = $(scrollerS);
      const mover = $(moverS);
      const topCont = $(topContS);
      const botCont = $(botContS);
      const modalElm = $(modalSelc);

      const switchToTop = ()=>{
        if (!mover.hasClass("switcher_top")) {
          // apply one time
          mover.removeClass("switcher_bot");
          mover.addClass("switcher_top");
          mover.hide('mid', null, () => {
              topCont.get(0).appendChild(mover.get(0));
              mover.show();
          });
        }
      };

      const switchToBot = ()=>{
        if (!mover.hasClass("switcher_bot")) {
          mover.toggleClass("switcher_top");
          mover.addClass("switcher_bot");
          mover.hide('mid', null, () => {
              botCont.get(0).appendChild(mover.get(0));
              mover.show();
          });
        }
      };

      scroll.off("scroll");
      modalElm.off('hidden.bs.modal');
      scroll.on("scroll", () => {
          if ((scroll.scrollTop() + scroll.get(0).offsetHeight) + 300 >= scroll.get(0).scrollHeight) {
            // apply switch 1 time per position UI and Performance (ex if scrolled bot no repeat until back top then scrolled bot)
            switchToBot();
          } else {
            switchToTop();
          }
      });
      modalElm.on('hidden.bs.modal', switchToTop);
  }
}

$(document).ready(async function(){
    applyHoverEffect();
    $('form:not(".no_submit_hide")').on('submit', (e)=>{
      const submitBtn = $(e.currentTarget).find('[type="submit"]').eq(0);
      if (submitBtn.length) {
        $(e.currentTarget).find('[type="submit"]').remove();
        console.log('done');
      }
    });
});



