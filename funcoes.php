<?php 


	/*
		Return a array with:
		- Number of dozens defined for $t;
			Ex: $var = generateRandom();
	*/
	function generateRandom($a = [], $t = 14) : array
	{

		$n = rand(1,25);

		if(in_array($n, $a, true))
		{
			return generateRandom($a);
		}
		else
		{
			array_push($a, $n);
		}

		sort($a);

		(count($a) <= $t) ? $res = generateRandom($a) : $res = $a;

		return $res;

	}

	/* 
		Return a array with:
		- Total of integer;
			Ex: $var = frame(array)['total_frame'];
		- Dozens in frame;
			Ex: $var = frame(array)['dozens_frame'];

	*/
	function frame($a) : array
	{
		$m = [1,2,3,4,5,6,10,16,20,21,22,23,24,25];

		$d = [];

		foreach ($a as $v)
		{
			(in_array($v, $m) == true) ? array_push($d, $v) : NULL ;
		}

		$ret = [
			'total_frame' => count($d),
			'dozens_frame' => $d
		];

		return $ret;
	}


	/* 
		Return a array with:
		- Total of odd;
			Ex: $var = oddEven(array)['odd'];
		- Total of even;
			Ex: $var = oddEven(array)['even'];
		- Inters odd found $a (array);
			Ex: $var = oddEven(array)['total_odd'];
		- Inters even found $a (array);
			Ex: $var = oddEven(array)['total_even'];

	*/
	function oddEven($a) : array
	{
		foreach ($a as $v) {
			if($v % 2 == 0){
				$even[] = $v;
			}else{
				$odd[] = $v;
			}
		}

		$ret = [
			'odd' => $odd,
			'even' => $even,
			'total_odd' => count($odd),
			'total_even' => count($even)
		];

		return $ret;
	}

	/* 
		Return a array with:
		- Total of prime numbers;
			Ex: $var = oddEven(array)['total_prime'];
		- Dozens of prime numbers;
			Ex: $var = oddEven(array)['dozens_prime'];

	*/
	function primeNumber($a) : array
	{

		$p = [2,3,5,7,11,13,17,19,23];

		$d = [];

		foreach ($a as $v)
		{
			(in_array($v, $p) == true) ? array_push($d, $v) : NULL ;
		}

		$ret = [
			'total_prime' => count($d),
			'dozens_prime' => $d
		];

		return $ret;
	}

	/* 
		Return a array with:
		- Sequence of numbers;
			Ex: $var = print_r(sequence(array));
	*/
	function sequence(array $a) : array
	{

		$s = [];
		$arr = [];

		foreach ($a as $key => $v) {
			array_push($arr, $v);

			if(!empty($a[$key + 1]) && $a[$key + 1] != $v + 1)
			{
				array_push($s, $arr);
				$arr = array();
			}
		}

		array_push($s, $arr);

		return $s;
	}



	

?>