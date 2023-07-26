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


/* (searchComponent) simple full jquery/html dom function that can complete search for any number of database columns 
eg:99m and html cards search done using DOM so it speed after setup like DOM selector (no css required and work with bs4 and not remove elements or styles)
*/
/* this addon used to enable calling this function multiple times to handle the selectors */
function searchComponent(speed='slow',easing='swing', cp=function(){return true;}, addon='', condition='='){
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
        
      };

      /* event listener for search (all hide actions) */
      $(`form#search_form${addon}`).on('submit', (event)=>{
        event.preventDefault();
        /* to allow reaserch not pass cp (clean and old search which hide cards, before start new search) */
        cancelSearch(speed, easing, ()=>{});
        
        const searchValue = $(`#search_value${addon}`).val().trim();
        const searchColumn = $(`#search_by${addon}`).val().trim();
        const dataAttrName = dataSearchAttrs[searchColumn];
        if (dataAttrName && searchValue){
          /* html selector search condition set */
          const targetCards = $(`.searching_card${addon}[${dataAttrName}${condition}'${searchValue}']`);
          const targetCardsArr = $(targetCards).toArray();
          $(`.searching_card${addon}`).each( (s, searchingCard)=>{
            if (!targetCardsArr.includes($(searchingCard)[0])){
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
      return true;
    }
  
    /* if there were a form but no have inputs or not valid for any reason preventdefault submision as it js form*/
    stopSearchForm();
    console.log('unable to start search component');
    return false;
  }


/* function to dynamic fill wtform for delete any model using it's id and set dynamic url for form aswell (can used in any page) */
function deleteWtformsModalProccess(dataAttId, formId, idInputId, modalId) {
    $(".wtform_modal_deletebtn").on('click', (event) => {
        if ($(event.currentTarget).length) {
            const formAction = String($(event.currentTarget).attr('data-url')).trim();
            const dashboardId = String($(event.currentTarget).attr(dataAttId)).trim();
            if ($(`#${formId}`).length && $(`#${formId} input#${idInputId}`).length && formAction && dashboardId) {
                /* set target id and action url of delete model */
                $(`#${formId} input#${idInputId}`).val(dashboardId);
                $(`#${formId}`).attr('action', formAction);
            }
        }
    });

    $(`#${modalId}`).on('hidden.bs.modal', () => {
        if ($(`#${formId}`).length) {
            $(`#${formId}`).attr('action', '');
        }
        if ($(`#${formId} input#${idInputId}`).length) {
            $(`#${formId} input#${idInputId}`).val('');
        }
    });
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


  let pagantionHTML = '<ul class="pagination">';

  let previousClasses = (currentBtnGroupI == 0) ? 'previous page-item disabled' : 'previous page-item';
  let previousPaginationGroupI = (currentBtnGroupI > 0) ? currentBtnGroupI - 1 : 0;
  pagantionHTML += `<li class="${previousClasses}"><button type="button" class="page-link">Previous</button></li>`;

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
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-platform-id') && $("#name_edit").length && $("#platform_id_edit").length && $(`#edit_platform_form`) && $(event.currentTarget).attr('data-url') && $(event.currentTarget).attr('data-platform-name')) {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const platform_id = String($(event.currentTarget).attr('data-platform-id')).trim();
        const platform_name = String($(event.currentTarget).attr('data-platform-name')).trim();      
        $("#platform_id_edit").val(platform_id);
        $("#name_edit").val(platform_name);
        $(`#edit_platform_form`).attr('action', action_url);
    }
  });

  $(`#edit_platform_form`).on('hidden.bs.modal', () => {
    if ($("#platform_id_edit").length){
      $("#platform_id_edit").val("");
    }
    if ($("#name_edit").length){
      $("#name_edit").val("");
    }
    $(`#edit_platform_form`).attr('action', '');
  });
}


function fillEditLocation(){
  $(".edit_location").on('click', (event)=>{
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-location-id') && $("#location_name_edit").length && $("#location_id_edit").length && $(`#edit_location_form`) && $(event.currentTarget).attr('data-url') && $(event.currentTarget).attr('data-location-name')) {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const location_id = String($(event.currentTarget).attr('data-location-id')).trim();
        const location_name = String($(event.currentTarget).attr('data-location-name')).trim();      
        $("#location_id_edit").val(location_id);
        $("#location_name_edit").val(location_name);
        $(`#edit_location_form`).attr('action', action_url);
    }
  });

  $(`#edit_location_form`).on('hidden.bs.modal', () => {
    if ($("#location_id_edit").length){
      $("#location_id_edit").val("");
    }
    if ($("#location_name_edit").length){
      $("#location_name_edit").val("");
    }
    $(`#edit_location_form`).attr('action', '');
  });
}


function fillEditBin(){
  $(".edit_bin").on('click', (event)=>{
    if ($(event.currentTarget).length && $(event.currentTarget).attr('data-bin-id') && $("#bin_name_edit").length && $("#bin_id_edit").length && $(`#edit_bin_form`) && $(event.currentTarget).attr('data-url') && $(event.currentTarget).attr('data-bin-name')) {
        const action_url = String($(event.currentTarget).attr('data-url')).trim();
        const bin_id = String($(event.currentTarget).attr('data-bin-id')).trim();
        const bin_name = String($(event.currentTarget).attr('data-bin-name')).trim();      
        $("#bin_id_edit").val(bin_id);
        $("#bin_name_edit").val(bin_name);
        $(`#edit_bin_form`).attr('action', action_url);
    }
  });

  $(`#edit_bin_form`).on('hidden.bs.modal', () => {
    if ($("#bin_id_edit").length){
      $("#bin_id_edit").val("");
    }
    if ($("#bin_name_edit").length){
      $("#bin_name_edit").val("");
    }
    $(`#edit_bin_form`).attr('action', '');
  });
}


/* integerted with search throw 1 event cancel search, and visible elements (searchComponent use display none for process search result) */
function multipleSelectComponent(checkboxSelector='', dataLabel='', actionModals=[], selectAllSelector=''){
  let checkedCheckBoxes = [];
  let selectedValues = [];
  let selectedLabels = [];
  // true means can start select all
  let selectAllStatus = true;

  /* validate actions modals objects (to make function dyanmic focus only with select provid array of objects for each action modal eg:delete_catalogue, update_catalogue_catagory, or any other action provided) */
  let allActionsReady = (Array.isArray(actionModals) && actionModals.length > 0) ? true : false;
  for (let a=0; a<actionModals.length; a++){
   let actionModal = actionModals[a];
   if (!(
     actionModal.modalId && actionModal.actionLabesSelctor && actionModal.formInputSelector &&
     actionModal.startActionBtn && $(actionModal.modalId).length && 
     $(actionModal.actionLabesSelctor).length && $(actionModal.formInputSelector).length && $(actionModal.startActionBtn).length
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
   
   $(checkboxSelector).on('change', function(e){      

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

   });

   actionModals.forEach( (actionModal)=>{
       $(actionModal.modalId).on('shown.bs.modal', function(e) {
         
       
       /* set action form input value */
       $(actionModal.formInputSelector).val(selectedValues.join(","));
 
       $(actionModal.actionLabesSelctor).html("");
 
       // display total element text if provided
       if (actionModal.totalElement && $(actionModal.totalElement).length){
         $(actionModal.totalElement).text(selectedValues.length);
       }
     
       // display labels
       let actionLabesHtml = '';
       selectedLabels.forEach( (labelText)=>{
         actionLabesHtml += `<span class="badge badge-secondary mr-1 mt-1">${labelText}</span>`;
       });
       $(actionModal.actionLabesSelctor).html(actionLabesHtml);
     });
   
     actionModals.forEach( (actionModal)=>{
       $(actionModal.modalId).on('hide.bs.modal', function(e) {
         // empty labels
         $(actionModal.actionLabesSelctor).html("");
         // empty total elements text if exist
         if (actionModal.totalElement && $(actionModal.totalElement).length){
           $(actionModal.totalElement).text("0");
         }
         // if selectAll exist reset it          
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
  } else {
   console.log('multipleSelectComponent not started');
  }
}
$(document).ready(async function(){
    applyHoverEffect();
});


