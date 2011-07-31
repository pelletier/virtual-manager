## Virtual-manager shell script.
## If you source it, it will create a custom `vm` function to wrap both the
## Python script and the `vmcd` hack

# This is where the current script is.
VM_DIR=$(dirname "${BASH_SOURCE[0]}")

function _vmcd {
    VM_P=$(python "$VM_DIR/vm_cd.py" "$1")
    if [ "$VM_P" = "-1" ]
    then
        echo "VM $1 does not exist."
    else
        cd "$VM_P"
    fi
}

function vm {
    if [ "$1" = "cd" ]
    then
        _vmcd $2
    else
        python "$VM_DIR/virtual_manager.py" "$@"
    fi
}
