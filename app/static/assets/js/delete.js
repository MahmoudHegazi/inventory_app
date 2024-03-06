const svgMaker = {
	svg: document.querySelector("#main"),
	topShapes: 0,
	botShapes: 0,
	rightShapes: 0,
	centerMain: 0,
	h: 700,
	w: 1000,
	reactAngle: (...args) => {
		let deviceInfos = '';
		args.forEach((deviceInfoArg, i) => {
			if (i == 0) {
				deviceInfos += `<p xmlns="http://www.w3.org/1999/xhtml">${deviceInfoArg}</p>`;
			} else {
				deviceInfos += `<p xmlns="http://www.w3.org/1999/xhtml" style="margin-top:-15px;">${deviceInfoArg}</p>`;
			}

		});
		if (svgMaker.centerMain === 0) {
			const height = (svgMaker.h - 546) + 182;
			const resultSvg = `<rect width="728" height="${height}" x="0" y="182" rx="20" ry="20" fill="white" stroke="black" stroke-width="1px" />
             <switch>
<foreignObject x="20" y="273" width="250" height="200">
${deviceInfos}
</foreignObject>
<text x="20" y="270">AAAPUSCA267-R01-BUR-ATO</text>
<text x="20" y="290">65440</text>
<text x="20" y="310">Loopback0 10.111.251.74</text>
<text x="20" y="330">Loopback300 10.43.218.39</text>
</switch>

    
    
             `;
			svgMaker.svg.innerHTML += resultSvg;
			return resultSvg;
		} else {
			return false;
		}
	},
	circleTopComponent: (gioPort = '', ipTxt = '', centerTxt = '', protocol = '', pid = '') => {
		if (svgMaker.topShapes < 4) {

			// if not draw the reactangle first

			// can also safe previous shape but this rule
			const cx = (95 * svgMaker.topShapes) + (95 * (svgMaker.topShapes + 1));
			console.log('currentX', cx);
			//const cx = svgMaker.topShapes * 190;
			// react started from the first redius 90 not full circle as it exist within the first part of circle
			const rcx = ((95 * (svgMaker.topShapes)) + (95 * (svgMaker.topShapes + 1)) - 95);
			const rectCX = rcx + 20;
			const ipTextCX = rectCX + 20;
			svgMaker.topShapes += 1;
			const resultSvg = `<!-- circle shape top -->
    <!-- cx=shapes*(190) -->
    <circle r="90" cx="${cx}" cy="91"  stroke="black" stroke-width="1" fill="white" stroke-dasharray="10,5"  />
    <!-- x=cx -->
    <text x="${cx}" y="10" dominant-baseline="middle" text-anchor="middle" style="font-weight:bold;font-size:12px;" >
      <tspan x="${cx}" dy="1em">${protocol}</tspan>
      <tspan x="${cx}" dy="1em">${pid}</tspan>
    </text>
    <!-- (total_shapes*95) + 20 -->
    <rect width="150" height="35"  x="${rectCX}" y="60" rx="3" ry="3" fill="white" style="stroke:black;stroke-width:1;" />
    <!-- x=rect.x+20, y=rect.y+20 fixed -->
    <text x="${ipTextCX}" y="80">${centerTxt}</text>
    <!-- x1=cx  y1=cy  y2= cy*2 -->
    <line x1="${cx}" y1="95" x2="${cx}" y2="182" style="stroke:black;stroke-width:4" />
    <text x="${cx}" y="182" dominant-baseline="middle" text-anchor="middle">
      <tspan x="${cx}" dy="1em">${gioPort}</tspan>
      <tspan x="${cx}" dy="1em">${ipTxt}</tspan>
    </text>
  <!-- circle shape end -->`;
			svgMaker.svg.innerHTML += resultSvg;
			return resultSvg;
		} else {
			return false;
		}
	},
	rectangularTopComponent: (gioPort = '', ipTxt = '', centerTxt = '') => {
		if (svgMaker.topShapes < 4) {


			// can also safe previous shape but this rule
			const cx = (95 * svgMaker.topShapes) + (95 * (svgMaker.topShapes + 1));
			console.log('currentX', cx);
			//const cx = svgMaker.topShapes * 190;
			// react started from the first redius 90 not full circle as it exist within the first part of circle
			const rcx = ((95 * svgMaker.topShapes) + (95 * (svgMaker.topShapes + 1)) - 95);
			const rectCX = rcx + 20;
			const ipTextCX = rectCX + 64;
			svgMaker.topShapes += 1;
			const resultSvg = `
    <rect width="150" height="35"  x="${rectCX}" y="60" rx="3" ry="3" fill="white" style="stroke:black;stroke-width:1;" />
    <!-- x=rect.x+20, y=rect.y+20 fixed -->
    <text x="${ipTextCX}" y="80">${centerTxt}</text>
    <!-- x1=cx  y1=cy  y2= cy*2 -->
    <line x1="${cx}" y1="95" x2="${cx}" y2="182" style="stroke:black;stroke-width:4" />
    <!-- x==cx -->
    <text x="${cx}" y="182" dominant-baseline="middle" text-anchor="middle">
      <tspan x="${cx}" dy="1em">${gioPort}</tspan>
      <tspan x="${cx}" dy="1em">${ipTxt}</tspan>
    </text>`;
			svgMaker.svg.innerHTML += resultSvg;
			return resultSvg;
		} else {
			return false;
		}
	},
	circleBotComponent: (gioPort = '', ipTxt = '', centerTxt = '', protocol = '', pid = '') => {
		if (svgMaker.botShapes < 4) {


			// can also safe previous shape but this rule add before first to avoid what will ignored ex it start 0 but there are 2 margin so only add the 2 mrgin , second end with full current and previous mrgin so 1+ 3 for example 4
			const cx = (95 * svgMaker.botShapes) + (95 * (svgMaker.botShapes + 1));
			console.log('currentX', cx);
			//const cx = svgMaker.botShapes * 190;
			// react started from the first redius 90 not full circle as it exist within the first part of circle
			const rcx = ((95 * svgMaker.botShapes) + (95 * (svgMaker.botShapes + 1)) - 95);
			const rectCX = rcx + 20;
			const ipTextCX = rectCX + 20;
			const yFullR = svgMaker.h - 182;
			const yHalfR = svgMaker.h - 91;
			const textTop = (svgMaker.h - 182) - 50;
			const textinRect = yHalfR + 20;
			const lastText = textinRect + 20;

			svgMaker.botShapes += 1;
			const resultSvg = `<!-- circle shape bottom -->
    <!-- cx=shapes*(190) -->
    <text x="${cx}" y="${textTop}" dominant-baseline="middle" text-anchor="middle">
      <tspan x="${cx}" dy="1em">${gioPort}</tspan>
      <tspan x="${cx}" dy="1em">${ipTxt}</tspan>
    </text>
    <circle r="90" cx="${cx}" cy="${yHalfR}"  stroke="black" stroke-width="1" fill="white" stroke-dasharray="10,5"  />
    
    <!-- x1=cx  y1=cy  y2= cy*2 -->
    <line x1="${cx}" y1="${yFullR}" x2="${cx}" y2="${yHalfR}" style="stroke:black;stroke-width:4" />
    <!-- (total_shapes*95) + 20 -->
    <rect width="150" height="35"  x="${rectCX}" y="${yHalfR}" rx="3" ry="3" fill="white" style="stroke:black;stroke-width:1;" />
    <!-- x=rect.x+20, y=rect.y+20 fixed -->
    <text x="${ipTextCX}" y="${textinRect}" dominant-baseline="middle">${centerTxt}</text>
    
    <!-- x=cx -->
    <text x="${cx}" y="${lastText}" dominant-baseline="middle" text-anchor="middle" style="font-weight:bold;" >
      <tspan x="${cx}" dy="1em">${protocol}</tspan>
      <tspan x="${cx}" dy="1em">${pid}</tspan>
    </text>
`;
			svgMaker.svg.innerHTML += resultSvg;
			return resultSvg;
		} else {
			return false;
		}
	},
	rectangularBotComponent: (gioPort = '', ipTxt = '', centerTxt = '') => {
		if (svgMaker.botShapes < 4) {


			// can also safe previous shape but this rule
			const cx = (95 * svgMaker.botShapes) + (95 * (svgMaker.botShapes + 1));
			console.log('currentX', cx);
			//const cx = svgMaker.botShapes * 190;
			// react started from the first redius 90 not full circle as it exist within the first part of circle
			const rcx = ((95 * svgMaker.botShapes) + (95 * (svgMaker.botShapes + 1)) - 95);
			const rectCX = rcx + 20;
			const ipTextCX = rectCX + 64;

			const yFullR = svgMaker.h - 182;
			const yHalfR = svgMaker.h - 91;
			const textTop = (svgMaker.h - 182) - 50;
			const textinRect = yHalfR + 20;

			svgMaker.botShapes += 1;
			const resultSvg = `<!-- reactangle shape bottom -->
    <text x="${cx}" y="${textTop}" dominant-baseline="middle" text-anchor="middle">
      <tspan x="${cx}" dy="1em">${gioPort}</tspan>
      <tspan x="${cx}" dy="1em">${ipTxt}</tspan>
    </text>
    <!-- x1=cx  y1=cy  y2= cy*2 -->
    <line x1="${cx}" y1="${yFullR}" x2="${cx}" y2="${yHalfR}" style="stroke:black;stroke-width:4" />
    <!-- (total_shapes*95) + 20 -->
    <rect width="150" height="35"  x="${rectCX}" y="${yHalfR}" rx="3" ry="3" fill="white" style="stroke:black;stroke-width:1;" />
    <!-- can make types of align, ip or long text,cu like -->
    <!-- x=rect.x+63, y=rect.y+20 fixed -->
    <text x="${ipTextCX}" y="${textinRect}" dominant-baseline="middle" style="font-size:16px;">${centerTxt}</text>
    <!-- reactangle shape bottom end -->`;
			svgMaker.svg.innerHTML += resultSvg;
			return resultSvg;
		} else {
			return false;
		}
	},
	ellipseRightComponent: (gioPort = '', ipTxt = '', centerTxt = '', protocol = '', pid = '') => {
		if (svgMaker.rightShapes === 0) {


			const cx = (svgMaker.w - 130) - 10;
			const rectX = cx - 34;
			const txtX = cx - 14;
			const lineStart = cx - 132;
			const leftTxt = cx - 194;
			//const lineX = 

			const cy = svgMaker.h / 2;
			const txt1 = cy - 80;
			const txt2 = cy - 20;
			const txt3 = cy + 3;
			const txt4_1 = cy - 5;
			const txt4_2 = cy - 3;
			const txt5 = cy - 30;

			const resultSvg = `<!-- ellipse shape right -->
    <ellipse cx="${cx}" cy="${cy}" rx="130" ry="86" stroke="black" stroke-width="1" fill="white" stroke-dasharray="10,5" />
    <text x="${cx}" y="${txt1}" dominant-baseline="middle" text-anchor="middle" style="font-weight:bold;" >
      <tspan x="${cx}" dy="1em">${protocol}</tspan>
      <tspan x="${cx}" dy="1em">${pid}</tspan>
    </text>
    <!-- cy - 20 -->
    <rect width="150" height="35"  x="${rectX}" y="${txt2}" rx="3" ry="3" fill="white" style="stroke:black;stroke-width:1;" />
    <!-- cy + 3 -->
    <text x="${txtX}" y="${txt3}">${centerTxt}</text>
    <!-- cy - 5 cy - 3 -->
    <line x1="${lineStart}" y1="${txt4_1}" x2="${rectX}" y2="${txt4_2}" style="stroke:black;stroke-width:4" />
    <!-- cy-30 -->
    <text x="${leftTxt}" y="${txt5}" dominant-baseline="middle" text-anchor="middle">
      <tspan x="${leftTxt}" dy="1em">${gioPort}</tspan>
      <tspan x="${leftTxt}" dy="1em">${ipTxt}</tspan>
    </text>
    <!-- circle shape end -->`;
			svgMaker.svg.innerHTML += resultSvg;
			svgMaker.rightShapes += 1;
			return resultSvg;
		} else {
			return false;
		}
	},

	rectangularRightComponent: (gioPort = '', ipTxt = '', centerTxt = '') => {
		if (svgMaker.rightShapes === 0) {



			const cx = (svgMaker.w - 130) - 10;
			const rectX = cx - 34;
			const txtX = cx - 14;
			const lineStart = cx - 132;
			const leftTxt = cx - 194;
			const txtMainX = rectX + 64;


			const cy = svgMaker.h / 2;
			const txt1 = cy - 80;
			const txt2 = cy - 20;
			const txt3 = cy + 3;
			const txt4_1 = cy - 5;
			const txt4_2 = cy - 3;
			const txt5 = cy - 30;

			svgMaker.rightShapes += 1;
			const resultSvg = `<!-- reactangle shape right -->

    <rect width="150" height="35"  x="${rectX}" y="${txt2}" rx="3" ry="3" fill="white" style="stroke:black;stroke-width:1;" />
    <!-- cy + 3 -->
    <text x="${txtMainX}" y="${txt3}">${centerTxt}</text>
    <!-- cy - 5 cy - 3 -->
    <line x1="${lineStart}" y1="${txt4_1}" x2="${rectX}" y2="${txt4_2}" style="stroke:black;stroke-width:4" />
    <!-- cy-30 -->
    <text x="${leftTxt}" y="${txt5}" dominant-baseline="middle" text-anchor="middle">
      <tspan x="${leftTxt}" dy="1em">${gioPort}</tspan>
      <tspan x="${leftTxt}" dy="1em">${ipTxt}</tspan>
    </text>
    <!-- reactangle shape end -->`;
			svgMaker.svg.innerHTML += resultSvg;
			return resultSvg;
		} else {
			return false;
		}
	},
	processITText: (txt = '') => {

		let deviceData = [];
		let interfaces = [];
		const data = {
			deviceData: [],
			interfaces: []
		};
		if (txt && typeof(txt) === 'string' && txt.length > 0) {
			txt = txt.trim();
			// dynamic strict split
			const deviceAndInterce = Array.from(txt.trim().split(new RegExp('device\[\s|\n|\r|\r\n]*:\s*[\1n|\r|\r\n]*|interfaces[\s|\n|\r|\r\n]*:\s*[\n|\r|\r\n]*', 'ig'))).filter((txtArg) => {
				return txtArg && txtArg.trim() != '';
			});
			alert(deviceAndInterce.length);
			console.log(deviceAndInterce);
			if (deviceAndInterce.length >= 2) {
				const deviceLines = deviceAndInterce[0].trim();
				const interfaceLines = deviceAndInterce[1].trim();
				if (deviceLines.length > 0) {
					// dynamic split
					data.deviceData = Array.from(deviceLines.split(new RegExp('\n|\r|\r\n')).filter((f1Txt) => {
						return f1Txt && f1Txt.trim() != '';
					}));
				}

				if (interfaceLines.length > 0) {
					data.interfaces = Array.from(interfaceLines.split(new RegExp('\n|\r|\r\n')).filter((f1Txt) => {
						return f1Txt && f1Txt.trim() != '';
					}));;
				}
				return data;

			} else {
				// fix with simple split for empty devices or interfaces
				const textSplit2 = txt.trim().split(new RegExp('interfaces[\s\n|\r|\r\n]*:\s*[\n|\r|\r\n]{0,}', 'ig'));
				if (textSplit2.length == 2) {

					let deviceTxt = textSplit2[0].replace(new RegExp('device[\s|\n|\r|\r\n]*:[\n|\r|\r\n]*', 'ig'), '');
					let interfaces = textSplit2[1];

					data.deviceData = Array.from(deviceTxt.split(new RegExp('\n|\r|\r\n')).filter((f1Txt) => {
						return f1Txt && f1Txt.trim() != '';
					}));
					data.interfaces = Array.from(interfaces.split(new RegExp('\n|\r|\r\n')).filter((f1Txt) => {
						return f1Txt && f1Txt.trim() != '';
					}));;
					return data;

				} else {
					console.log("invalid text provided it may include aditional not needed part");
					return false;
				}

			}
		} else {

			return false;

		}
	},
	interFaceTypes: {
		circle: {
			top: function() {
				return svgMaker.circleTopComponent;
			},
			right: function() {
				return svgMaker.ellipseRightComponent;
			},
			below: function() {
				return svgMaker.circleBotComponent;
			}
		},
		reactangle: {
			top: function() {
				return svgMaker.rectangularTopComponent;
			},
			right: function() {
				return svgMaker.rectangularRightComponent;
			},
			below: function() {
				return svgMaker.rectangularBotComponent;
			}
		}
	},
	addInterface: (interfaceTxt = '') => {
		if (typeof(interfaceTxt) === 'string' && interfaceTxt) {
			let interFaceInfo = interfaceTxt.trim().split(" ");
			//alert(interFaceInfo.length);
			let interFaceType = '';
			let position = '';
			let centerTxt = '';
			let argus = [];
            let added = false;
			const positions = ['right', 'top', 'below'];

			let drawMethod = null;
			if (interFaceInfo.length >= 6) {

				/* small dynamic rgex fix https://stackoverflow.com/questions/70059085/javascript-regular-expression-split-string-by-periods-not-in-double-quotes */


				if (interFaceInfo.length > 6) {
					// not it can work same as split(" ") and better but for more better use split unless issue
					const regex = /(?:[0-9]{1,3}\(.*\)|[^\s)])+(?:\s+$|\s^.*\))?/g;
					const str = interfaceTxt.trim();
					if (str.match(regex).length === 6) {
						// regex not able while it must so notice if anyissue
						interFaceInfo = Array.from(str.match(regex));
					}
				}

				// circle
				interFaceType = 'circle';
				const gioPort = interFaceInfo[0];
				const ipTxt = interFaceInfo[1];
				position = String(interFaceInfo[2]).trim().toLowerCase();
				centerTxt = interFaceInfo[3];
				const protocol = interFaceInfo[4];
				const pid = interFaceInfo[5];

				if (svgMaker.interFaceTypes.circle.hasOwnProperty(position) && typeof(svgMaker.interFaceTypes.circle[position]) === 'function') {
					drawMethod = svgMaker.interFaceTypes.circle[position]();

					if (typeof(drawMethod) === 'function') {
						const isAdded = drawMethod(gioPort, ipTxt, centerTxt, protocol, pid) != false;
                        added = isAdded != false;
					} else {
						console.log("invalid code object error");
						return false;
					}

				} else {
					console.log('invalid position circle:', position);
					return false;
				}

				//alert('circle');
			} else if (interFaceInfo.length == 4) {
                interFaceType = 'reactangle';
				const gioPort = interFaceInfo[0];
				const ipTxt = interFaceInfo[1];
				position = String(interFaceInfo[2]).trim().toLowerCase();
				centerTxt = interFaceInfo[3];

				if (svgMaker.interFaceTypes.reactangle.hasOwnProperty(position) && typeof(svgMaker.interFaceTypes.reactangle[position]) === 'function') {
					drawMethod = svgMaker.interFaceTypes.reactangle[position]();
					if (typeof(drawMethod) === 'function') {
						const isAdded = drawMethod(gioPort, ipTxt, centerTxt);
                        added = isAdded != false;
					} else {
						console.log("invalid code object error");
						return false;
					}

				} else {
					console.log('invalid position reactangle:', position);
					return false;
				}

				//alert('reactangle');
			} else {
				console.log("invalid interfaceTxt unknown circle or react");
				return false;
			}

            console.log(String(added), interfaceTxt);
            return added;

		} else {
			console.log("invalid interfaceTxt value must be strig");
			return false;
		}
	},
	start: function(txt) {
		// process text and get 2 data list
		const data = svgMaker.processITText(txt);
		// dynamic setup
		svgMaker.reactAngle(...data.deviceData);

		let success = true;
		data.interfaces.forEach((interface) => {
            const interfaceAdded = svgMaker.addInterface(interface);
			if (!interfaceAdded) {
				console.log('found not successfull interface', interface, interfaceAdded);
				success = false;
			}
		});
        console.log(this.exportSVG());
		return success;

	},
    exportSVG: ()=>{
      return document.querySelector("#main").outerHTML.trim();
    }

};

/*

Device:
AAAPUSCA267-R01-BUR-ATO
65440
Loopback0 10.111.251.74
Loopback3000 10.43.218.39lolnexttype
hello world info extra

Interfaces:
Gi0/0/2.1 10.111.46.130 top 10.111.46.129 EBGP 13979


Gi0/0/1 10.48.225.187 right 10.48.225.186 IBGP 65440


Gi0/1/0.125 57.236.185.91 Below CU


Gi0/1/0.128 57.236.185.68 Below CU

Gi0/0/0 10.7.225.182 Below BUR-ATO-DSW1 OSPF 100(area 0)
*/


svgMaker.start(`Device:
AAAPUSCA267-R01-BUR-ATO
65440
Loopback0 10.111.251.74
Loopback3000 10.43.218.39
hello world extra

Interfaces:
Gi0/0/2.1 10.111.46.130 top 10.111.46.129 EBGP 13979


Gi0/0/1 10.48.225.187 right 10.48.225.186 IBGP 65440


Gi0/1/0.125 57.236.185.91 Below CU


Gi0/1/0.128 57.236.185.68 Below CU

Gi0/0/0 10.7.225.182 Below BUR-ATO-DSW1 OSPF 100(area 0)`);

//svgMaker.addInterface('Gi0/0/2.1 10.111.46.130 top 10.111.46.129 EBGP 13979');
//svgMaker.addInterface('Gi0/0/1 10.48.225.187 right 10.48.225.186 IBGP 65440');
//svgMaker.addInterface('Gi0/0/0 10.7.225.182 Below BUR-ATO-DSW1 OSPF 100(area 0)');
//svgMaker.addInterface('Gi0/1/0.125 57.236.185.200 right Hi');
//alert('Gi0/0/0 10.7.225.182 Below BUR-ATO-DSW1 OSPF 100(area 0)'.split(' ').length + 'here');
//svgMaker.circleTopComponent('255.255.255.255');
//svgMaker.circleTopComponent('255.255.255.255');
//svgMaker.circleBotComponent('BUR-ATO-DSW1');
//svgMaker.rectangularTopComponent('CU');
//svgMaker.rectangularBotComponent('CU');
//svgMaker.rectangularBotComponent('CU');
//svgMaker.rectangularBotComponent('CU');
//svgMaker.circleTopComponent('255.255.255.255');
//svgMaker.ellipseRightComponent('CU');
//svgMaker.addInterface('Gi0/1/0.125 57.236.185.91 Below CU');
//svgMaker.circleTopComponent('255.255.255.255', 1);
//alert(svgMaker.circleTopComponent('255.255.255.255', 2));

/*
svgMaker.circleTopComponent('255.255.255.255');
svgMaker.rectangularTopComponent('CU');
svgMaker.circleTopComponent('255.255.255.255');
svgMaker.circleBotComponent('BUR-ATO-DSW1');
svgMaker.circleBotComponent('BUR-ATO-DSW1');
svgMaker.circleBotComponent('BUR-ATO-DSW1');
svgMaker.rectangularBotComponent('CU');
*/
/*BUR-ATO-DSW1
svgMaker.circleTopComponent('255.255.255.255');
svgMaker.circleTopComponent('255.255.255.255');
svgMaker.circleTopComponent('255.255.255.255');
svgMaker.circleTopComponent('255.255.255.255');
*/