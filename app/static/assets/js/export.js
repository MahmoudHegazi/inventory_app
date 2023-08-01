const tables = ['catalogue', 'listing', 'order', 'purchase', 'supplier'];

let rowIndex = 0;
let filterColumns = ["id", "supplier_name"];
/*avail conditions const*/
conditions = [
    {label: 'Equal', value:'=', description: 'Equal To the speacfied Value'},
    {label: 'Not Equal', value:'!=', description: 'not Equal To the speacfied Value'},
    {label: 'Greater Than', value:'>', description: 'Greater than the speacfied Value'},
    {label: 'Less Than', value:'<', description: 'Less than the speacfied Value'},
    {label: 'Greater Than or Equal', value:'>=', description: 'Greater than the speacfied Value or equal to it'},
    {label: 'Less Than or Equal', value:'<=', description: 'Less than or equal to the specified value.'},
    {label: 'Start With', value:'val%', description: 'The result content starts with the specified value.'},
    {label: 'End With', value:'%val', description: 'The result content ends with the specified value.'},
    {label: 'Contains', value:'%val%', description: 'The result content contains the specified value.'}
];


/* helpers */
function makeReadable(str){
  /*Ai Replace 'test-1_something_1' --> 'Test 1 Something 1'*/
  let aiStr = str.replace(/(:?\_|\-|\.)([a-z0-9])/ig, function (g, operator, val, index, original) {
    return " "+g[1];
  });
  /*captlize first char in word*/
  return aiStr.split(" ").map((word)=>{
        return (word ? word[0].toUpperCase()+word.slice(1) : word);
    }).join(" ");
}



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





function addFilterRow(){
  if ($("#filter_form_cont").length && filterColumns.length){
    const rowId = `row_${rowIndex}`;
    $("#filter_form_cont").append(`
    <div class="row mb-2 rounded shadow pb-2 filter_row p-2 ml-2 mr-2" id="${rowId}">
      <div class="col-4">
        <!-- rowID make function more dynamic to be called from any where for later updates -->
        <select class="form-control column_select" name="column[]"  onchange="fillConditionSelect('#${rowId}')" required="required">
           <option>Column</option>
        </select>
      </div>
      <div class="col">
        <select class="form-control condition_select" name="operator[]" required="required">
           <option value="">Operator</option>
        </select>
      </div>
      <div class="col">
        <input type="text" class="form-control" placeholder="Value" name="value[]">
      </div>
      <div class="col-1">
        <button type="button" class="btn btn-danger btn-sm" data-row="#${rowId}" onclick="removeFilterRow(event)"><i class="fa fa-remove"></i></button>
      </div>
    </div>`);
    rowIndex += 1;
    fillColumnSelect(`#${rowId}`);
    return true;
  } else {
    console.log("can not add row missing filter_form, or columns empty, maybe ajax request not completed");
    return false;
  }
}



function removeFilterRow(event){
  if ($(event.currentTarget).length && $(event.currentTarget).attr('data-row') && $($(event.currentTarget).attr('data-row')).length){
    const selectedRow = $($(event.currentTarget).attr('data-row'));
    $(selectedRow).remove();
    return true;
  } else {
    console.log("can not remove row, row not found");
    return false;
  }
}

function emptyFilterData(){
    // empty old filter_columns loaded
    filterColumns = [];

  if ($(".filter_row").length){
    $(".filter_row").remove();
  }
}



function fillColumnSelect(rowSelector){
  if (rowSelector && $(rowSelector).length && $(`${rowSelector} select.column_select`).length && filterColumns.length)   {
     /*action*/
     const selectedColumnSelect = $(`${rowSelector} select.column_select`).eq(0);
     $(selectedColumnSelect).html('<option value="">Column</option>');
     
     let columnString = '';
     filterColumns.forEach( (colOption)=>{
       if (colOption && colOption){
          columnString += `<option value="${colOption}">${makeReadable(colOption)}</option>`;
       }       
     });
     $(selectedColumnSelect).append(columnString);
     return true;
  } else {
    
    /*this for safe empty select incase system/programing errors*/
    const selectedColumnSelect = $(`${rowSelector} select.column_select`);
    if ($(selectedColumnSelect).length){
      $(selectedColumnSelect).eq(0).html('<option value="">Column</option>');
    }
    console.log("can not fill filters invalid row selector, or missing select inputs or columns list empty");
    
    return false;
  }
}


function fillConditionSelect(rowSelector){
  if (conditions && rowSelector && $(rowSelector).length && $(`${rowSelector} .column_select`).length && $(`${rowSelector} .condition_select`).length ){
    const columnValue = $(`${rowSelector} .column_select`).eq(0).val();
    const conditionSelect = $(`${rowSelector} .condition_select`).eq(0);

    /*reset content of condition select before any action, incase empty val it will reset content too*/
    $(conditionSelect).html('<option value="">Condition</option>');
    
    if (columnValue){
        /*performance friendly way to add many options fast*/
        let conditionStr = '';
        conditions.forEach( (conditionObj)=>{
           conditionStr += `<option value="${conditionObj.value}" title="${conditionObj.description}">${conditionObj.label}</option>`;            
        });
        $(conditionSelect).append(conditionStr);
    }
    return true;
  } else {
    console.log("can not fill condition select row not found, or invalid row content, or invalid conditions const");
    
    /*this for safe empty select incase system/programing errors*/
    const conditionSelect = $(`${rowSelector} .condition_select`);
    if ($(conditionSelect).length){
      $(conditionSelect).eq(0).html('<option value="">Condition</option>');
    }
    return false;
  }
}


/* send ajax request to load filter data (set columns const) */
function getFilterData(url='', type='GET', data={}) {
    emptyFilterData();

    if (!$("#filter_content").length){
      console.log("missing filter_content element");
      return false;
    }
    $.ajax(url, {
        type: type,
        dataType: 'json',
        data: data,
        timeout: 5000,
        success: function(data, status, xhr) {          
          if (data && data.code == 200 && Array.isArray(data.data)){
             $("#filter_content").css("display", "block");
             /*!note user can export all data without filters*/
             filterColumns = data.data;
             //console.log("?", data.data);
          } else {
            let responseMsg = (data && data.message) ? data.message : 'The filter data could not be loaded, no Column selected';
            $("#filter_content").css("display", "none");
            displayAjaxError(responseMsg, "danger");
          }
          toggleLoadingCircle(on=false);
        },
        error: function(jqXhr, textStatus, errorMessage) {
            $("#filter_content").css("display", "none");
            /*usally this happend when no internet connection and server online or db connect issue*/
            displayAjaxError("The filter data could not be loaded, please refresh the page and try again later.", "danger");
            toggleLoadingCircle(on=false);
        }
    });
}


function exportTableStart(event){
  displayAjaxError(null);
  if ($(event.currentTarget).length && $(event.currentTarget).attr("data-table") && $(event.currentTarget).attr("data-url") && tables.includes($(event.currentTarget).attr("data-table")) && $('#filter_table_name').length && $("#table_name").length){
    const targetTable = $(event.currentTarget).attr("data-table");
    /* jinja2 url_for */
    const targetTableURL = $(event.currentTarget).attr("data-url");
    
    $('#filter_table_name').text(makeReadable(targetTable));
    $("#table_name").val(targetTable);
    
    toggleLoadingCircle(on=true);
    getFilterData(targetTableURL, 'GET');
    return true;
  } else {
    console.log("can not start exporting actions, missing currentTarget, or empty data-table found, or missing filter_table_name");
    toggleLoadingCircle(on=false);
    displayAjaxError('can not start exporting actions', "danger");
    return false;
  }
}
/* appli click event on open_export btns to load filter data once button clicked */


$(".open_export").on("click", exportTableStart);