<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as echarts from 'echarts';
	import { plotColors } from '$lib/constants';

	interface Props {
		plotData: any[];
		maxValue?: number | undefined;
		narrowBool?: boolean;
	}

	let { plotData, maxValue = undefined, narrowBool = false }: Props = $props();

	let myChartDiv: HTMLDivElement;
	let myChart: echarts.ECharts | null = null;
	let resizeHandler: () => void;
	let mounted = false;

	// Reactive derivations
	let myInterval = $derived.by(() => {
		if (maxValue && maxValue <= 11) {
			return 1;
		}
		return undefined;
	});

	let topPadding = $derived.by(() => (narrowBool ? 40 : 20));
	let rightPadding = $derived.by(() => (narrowBool ? 20 : 55));

	const dimensions = ['crawled_date'];

	function createSeries(data: any[]) {
		if (!data || data.length === 0) return [];

		const numberOfSeries = Object.keys(data[data.length - 1]).length - 1;
		const series = [];

		for (let i = 0; i < numberOfSeries; i++) {
			const seriesConfig: echarts.SeriesOption = {
				type: 'line',
				symbolSize: 10,
				smooth: true,
				emphasis: {
					focus: 'series'
				},
				lineStyle: {
					width: 2
				}
			};

			if (!narrowBool) {
				seriesConfig.endLabel = {
					show: true,
					formatter: '{a}',
					distance: 20,
					valueAnimation: true
				};
			}

			series.push(seriesConfig);
		}

		return series;
	}

	function createChartOption() {
		if (!plotData || plotData.length === 0) {
			return null;
		}

		const option: echarts.EChartsOption = {
			color: plotColors,
			backgroundColor: 'rgba(0, 0, 0, 0.3)',
			dataset: { source: plotData },
			dimensions: dimensions,
			grid: {
				left: 50,
				top: topPadding,
				right: rightPadding
				// bottom: 80
			},
			tooltip: {
				trigger: 'item'
			},
			xAxis: {
				type: 'category',
				splitLine: {
					show: true
				},
				axisLabel: {
					// margin: 10,
					fontSize: 18
				}
			},
			yAxis: {
				type: 'value',
				axisLabel: {
					margin: 10,
					fontSize: 18,
					formatter: '#{value}'
				},
				inverse: true,
				min: 1,
				interval: myInterval,
				max: maxValue
			},
			series: createSeries(plotData)
		};

		if (narrowBool) {
			option.legend = {};
		}

		return option;
	}

	function initializeChart() {
		if (!myChartDiv || !plotData || plotData.length === 0) {
			return;
		}

		// Dispose existing chart if it exists
		if (myChart) {
			myChart.dispose();
			myChart = null;
		}

		try {
			myChart = echarts.init(myChartDiv, 'dark');
			const option = createChartOption();

			if (option) {
				myChart.setOption(option);
			}

			// Set up resize handler
			if (resizeHandler) {
				window.removeEventListener('resize', resizeHandler);
			}

			resizeHandler = () => {
				if (myChart && !myChart.isDisposed()) {
					myChart.resize();
				}
			};

			window.addEventListener('resize', resizeHandler);
		} catch (error) {
			console.error('Error initializing chart:', error);
		}
	}

	onMount(() => {
		mounted = true;
		// Small delay to ensure DOM is fully ready
		setTimeout(() => {
			initializeChart();
		}, 10);
	});

	$effect(() => {
		if (mounted && plotData) {
			// Small delay to prevent rapid updates
			setTimeout(() => {
				initializeChart();
			}, 10);
		}
	});

	onDestroy(() => {
		mounted = false;
		if (resizeHandler) {
			window.removeEventListener('resize', resizeHandler);
		}
		if (myChart && !myChart.isDisposed()) {
			myChart.dispose();
			myChart = null;
		}
	});
</script>

<div class="w-full h-96" bind:this={myChartDiv}></div>
