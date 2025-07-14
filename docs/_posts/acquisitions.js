import Chart from '/assets/node_modules/chart.js/auto'
import annotationPlugin from '/assets/node_modules/chartjs-plugin-annotation';

Chart.register(annotationPlugin);

(async function() {

	const data = [
		{ hour: 0, pvpc: 0.14027}, 
		{ hour: 1, pvpc: 0.12684}, 
		{ hour: 2, pvpc: 0.12354000000000001}, 
		{ hour: 3, pvpc: 0.12389}, 
		{ hour: 4, pvpc: 0.12407}, 
		{ hour: 5, pvpc: 0.12677}, 
		{ hour: 6, pvpc: 0.14081}, 
		{ hour: 7, pvpc: 0.15497999999999998}, 
		{ hour: 8, pvpc: 0.17934999999999998}, 
		{ hour: 9, pvpc: 0.16266999999999998}, 
		{ hour: 10, pvpc: 0.19372}, 
		{ hour: 11, pvpc: 0.18952000000000002}, 
		{ hour: 12, pvpc: 0.19231}, 
		{ hour: 13, pvpc: 0.19133}, 
		{ hour: 14, pvpc: 0.14542}, 
		{ hour: 15, pvpc: 0.14515999999999998}, 
		{ hour: 16, pvpc: 0.1445}, 
		{ hour: 17, pvpc: 0.14562999999999998}, 
		{ hour: 18, pvpc: 0.19952}, 
		{ hour: 19, pvpc: 0.22491}, 
		{ hour: 20, pvpc: 0.24264}, 
		{ hour: 21, pvpc: 0.2474}, 
		{ hour: 22, pvpc: 0.19394999999999998}, 
		{ hour: 23, pvpc: 0.17969},];


   new Chart(
    document.getElementById('acquisitions'),
    {
      type: 'line',
      options: {
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: false
          }
        },
  	plugins: {
  	  annotation: {
  	    annotations: {
  	      point1: {
  	        type: 'point',
  	        xValue: 2,
  	        yValue: 0.124,
  	        backgroundColor: 'rgba(255, 99, 132, 0.25)'
  	      },
	     label1: {
		     type: 'label',
		     backgroundColor: 'rgba(245,245,245)',
		     xValue: 2,
          	     yValue: 0.124,
		     xAdjust: 100,
          	     yAdjust: -200,
		     content: ['Min: 0.124 (2:00)'],
		     textAlign: 'start',
	     	     callout: {
            	         display: true,
            	         side: 10 
          	     }
	     },
	     point2: {
  	        type: 'point',
  	        xValue: 21,
  	        yValue: 0.247,
  	        backgroundColor: 'rgba(255, 99, 132, 0.25)'
  	      },

	     label2: {
		     type: 'label',
		     backgroundColor: 'rgba(245,245,245)',
		     xValue: 21,
          	     yValue: 0.247,
		     xAdjust: -300,
          	     yAdjust: 0,
		     content: ['Max: 0.247 (21:00)'],
		     textAlign: 'start',
	     	     callout: {
            	         display: true,
            	         side: 10 
          	     }
	     }
	    }
  	  }
  	}
      },
      data: {
        labels: data.map(row => row.hour),
        datasets: [
          {
            label: 'Evolución precio para el día 2023-07-13',
            data: data.map(row => row.pvpc)
          }
        ]
      }
    }
  );

})();

