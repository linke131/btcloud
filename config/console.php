<?php
// +----------------------------------------------------------------------
// | 控制台配置
// +----------------------------------------------------------------------
return [
    // 指令定义
    'commands' => [
        'updateall' => 'app\command\UpdateAll',
        'decrypt' => 'app\command\DecryptFile',
        'clean' => 'app\command\Clean',
    ],
];
