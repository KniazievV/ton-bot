from aiogram.fsm.state import State, StatesGroup


class AddWalletStates(StatesGroup):
    wait_chain = State()
    wait_address = State()
    wait_name = State()
    wait_notify = State()
