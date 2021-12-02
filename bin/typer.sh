function typer {
    cmd=$1
    printf "\nLet me type this long command for you...\n\n"
    printf "$cmd\n\n"
    read -p "press enter to continue..."
    $cmd
}
