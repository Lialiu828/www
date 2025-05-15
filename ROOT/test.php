<?php
	require_once "uq/auth.php";
	auth_require();
	echo "<pre>";
	print_r(auth_get_payload());
	echo "</pre>";
?>
