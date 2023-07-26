function manyToManySelectorsComponent(locations_bins_data, actionsCbs=[]) {
    // by default locations_bins is hidden in begning, remove the options until user checks warehouse locations
    function clearBinsOptions(handle_hidden_select = false) {
        if ($("#locations_bins option").length) {
            $("#locations_bins option").each((_i, optionElm) => {
                $(optionElm).css('display', 'none');
                $(optionElm).attr('disabled', true);
            });
            if (handle_hidden_select) {
                $("#locations_bins").css('visibility', 'visible');
            }

        }
    }
    clearBinsOptions(handle_hidden_select = true);

    function displayBinOptionsByIds(optionsIds = [], selectId = '#locations_bins') {
        if (Array.isArray(optionsIds) && $(selectId).length) {
            let optionsByValSelector = `${String(selectId).trim()}`;
            let optionsArr = [];
            // provided is only value of options create string js selector to get all options
            optionsIds.forEach((optionId) => {
                if (optionId) {
                    let optionIdStr = String(optionId).trim();
                    optionsArr.push(`option[value='${optionIdStr}']`);
                }
            });

            // every time call function disable all older option and hide
            $(`${selectId} option`).css('display', 'none');
            $(`${selectId} option`).attr('disabled', true);

            // if not options not do any action with selector
            if (optionsArr.length > 0) {
                let optionsPart = optionsArr.join(",");
                optionsByValSelector += ` ${optionsPart}`;
                if (optionsByValSelector && $(optionsByValSelector).length) {
                    // display only selected options ids
                    $(optionsByValSelector).each((i, activeOption) => {
                        $(activeOption).removeAttr("disabled");
                        $(activeOption).removeAttr('style');
                    });
                }
            }
            return true;
        }
        return false;
    }

    function onWareHouseChange(event, handleBySelectedWareHouse = false) {

        let currentLocationBins = [];

        let isEvent = (event && $(event.target).length) ? true : false;
        if (isEvent || handleBySelectedWareHouse) {
            /* by using jinja2 provided data get the bins ids of selected warehouse_locations ids if any selected */
            let currentLocations = isEvent ? $(event.target).val() : $("#warehouse_locations").val();
            for (let l = 0; l < currentLocations.length; l++) {
                let selectedLocationId = parseInt(currentLocations[l]);
                for (let i = 0; i < locations_bins_data.length; i++) {
                    const currentLocationObj = locations_bins_data[i];
                    if (currentLocationObj.location == selectedLocationId && Array.isArray(currentLocationObj.bins)) {
                        currentLocationObj.bins.forEach((binId) => {
                            if (!currentLocationBins.includes(binId)) {
                                currentLocationBins.push(binId);
                            }
                        });
                        break;
                    }
                }
            }
        }
        // if bin ids, hide previous options and display only target options, will handled securly if no bin ids provided and hide, disbale old options
        displayBinOptionsByIds(currentLocationBins);
    }
    /* pased of each page and handle, eg calls for edit more than calls for add with diffrent arugments */
    if (Array.isArray(actionsCbs)){
        actionsCbs.forEach( (actionCB)=>{
            if (typeof(actionCB) === 'function'){
                actionCB(onWareHouseChange);
            }
        });
    }
}