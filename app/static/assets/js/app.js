/* Consts */
let noEffects = false;

/* Helper Functions */
function toggleLoadingCircle(on=false, displayCSS='', containerSelector='.content_container', imageSelector='.loading_circle'){
    if (noEffects === true){return false;}
    if (containerSelector != '' && imageSelector != ''){
        if ($(imageSelector).length && $(containerSelector).length) {
            /* start gif from begning */
            $(imageSelector).attr('src', $(imageSelector).attr('src'));
            console.log("hi");
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
    if (message==null && status == null){
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
function searchComponent(speed='slow',easing='swing', cp=function(){return true;}){
    const stopSearchForm = function(){
        if ($("form#search_form").length){
            $("form#search_form").on('submit', (ev)=>{
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
    if ($("body").length && $("form#search_form").length && $("#cancel_search[type='button']").length && $("#search_value").length &&
    $("#search_by option.search_column").length && typeof(cp) == 'function'){
      
      $("#cancel_search").hide();
      /*get dynamic data-search attributes and options value for column name*/
      $("#search_by option.search_column").each( (_i, dataSearchAttr)=>{
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
      $("body").append('<style>.hidden_search_card{ display: none !important }</style>');

      /* function to remove hidden cards with same effect and callback */
      function cancelSearch(speed, easing, cp){
        /* this for jquery works with bs4 becuase added css class with display:none !important so remove it and start make jquery effect that will run even if bs display element as it slow eg can not after display use: $(oldHidden).hide();*/
        const oldHidden = $(".hidden_search_card");
        $('.hidden_search_card').removeClass('hidden_search_card');
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
      $("form#search_form").on('submit', (event)=>{        
        event.preventDefault();
        /* to allow reaserch not pass cp (clean and old search which hide cards, before start new search) */
        cancelSearch(speed, easing, ()=>{});
        const searchValue = $("#search_value").val().trim();
        const searchColumn = $("#search_by").val().trim();
        const dataAttrName = dataSearchAttrs[searchColumn];
        if (dataAttrName && searchValue){
          const targetCards = $(`.searching_card[${dataAttrName}='${searchValue}']`);
          const targetCardsArr = $(targetCards).toArray();
          $(".searching_card").each( (s, searchingCard)=>{
            if (!targetCardsArr.includes($(searchingCard)[0])){
              /* this is how hide any bs4 (d-flex, row) with jquery effect css + callback*/
              $(searchingCard).hide(speed, easing, ()=>{
                $(searchingCard).addClass('hidden_search_card');
                /* call usercb */
                if (s+1 == $(".searching_card").length){
                  cp();                  
                }
              });
            }
          });
          $("#cancel_search").show();
        } else {
          cancelSearch(speed, easing, cp);
          $("#cancel_search").hide();
        }
      });

      /* cancel search event */
      $("#cancel_search").on('click', ()=>{
        cancelSearch(speed, easing, cp);
        $("#cancel_search").hide();
        $("#search_value").val('');
        
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

$(document).ready(async function(){
    applyHoverEffect();
});


