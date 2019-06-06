from time import clock
from functools import reduce
from random import shuffle
MAXSIZE = 50    # 棋盘最大尺寸


##################################################################
#  单元格
##################################################################
class Cell:
    def __init__(self, value_array):
        self.values = set(value_array)

    def __str__(self):
        return '<Cell>' + ' include: ' + str(self.values)
    __repr__ = __str__

    def __eq__(self, other):
        return True if self.values == other.values else False

    def __lt__(self, other):  # 小于
        return True if max(self.values) < min(other.values) else False

    def __gt__(self, other):  # 大于
        return True if min(self.values) > max(other.values) else False

    def copy(self):
        cell = Cell(tuple())
        cell.values = self.values.copy()
        return cell

    def set_value(self, value):   # 直接设置一个值，剔除其他可能的值
        if value not in self.values:
            raise FlyGameException('单元格已不包含{}这个值，无法设置。{}'.format(value, self.values))
        elif self.done:
            return
        self.values = {value}

    def del_value(self, value):     # 删除一个可能的值
        if value not in self.values:
            return
        elif self.done:
            raise FlyGameException('单元格最后一个值被删除，出错。', id(self))
        self.values = self.values - {value}
        # print('Delete value {}'.format(value))

    def del_values(self, values):  # 批量删除value
        for value in values:
            self.del_value(value)

    @property
    def done(self):     # 是否已完成
        return True if len(self.values) == 1 else False


##################################################################
#  游戏的数据
##################################################################
class Data:
    def __init__(self, size, value_array, init_data):
        if size > MAXSIZE:
            raise FlyGameException('棋盘的尺寸不能超过{}，请修改尺寸。'.format(MAXSIZE))
        self.size = size
        self.value_array = value_array
        self.cells = [Cell(value_array) for i in range(size**2)]
        if init_data:    # 添加初始化数据
            init_data = list(map(int, init_data))  # 将字符串改为整形列表
            if len(init_data) < size**2:  # 如果长度不够，后面补足0
                init_data = init_data + [0] * (size**2 - len(init_data))
            for index in range(size**2):
                if init_data[index] not in (0, '0', 'x', None):
                    self.cells[index].set_value(init_data[index])

    def __eq__(self, other):
        if self.size != other.size:
            return False
        for index in range(self.size**2):
            if self.cells[index] != other.data[index]:
                return False
        return True

    def copy(self):
        new_data = Data(0, self.value_array, None)
        new_data.size = self.size
        new_data.value_array = self.value_array
        new_data.cells = [self.cells[index].copy() for index in range(self.size**2)]
        return new_data

    def total_length(self):
        counts = map(lambda cell: len(cell.values), self.cells)
        return reduce(lambda a, b: a + b, counts)

    def is_finish(self):    # 是否完成
        return True if self.total_length() == self.size**2 else False

    def get_undone_cell(self):  # 找到一个未完成的单元格，返回索引，用于猜测
        for count in range(2, len(self.value_array)+1):
            for index in range(self.size**2):
                if len(self.cells[index].values) == count:
                    return index
        return None


##################################################################
#  游戏的规则
##################################################################
class Rule:
    @staticmethod
    def calculate(data, item):
        pass

    @staticmethod
    def is_wrong(data, item):
        return False

    @staticmethod
    def is_done(data, item):
        return False


##################################################################
#  游戏的Exception基类
##################################################################
class FlyGameException(Exception):
    def __init__(self, *args):
        super(FlyGameException, self).__init__(*args)
        self.content = args

    def __str__(self):
        return '<FlyException>\n' + str(self.args)


##################################################################
#  游戏类
##################################################################
class Game:
    def __init__(self, size=0):
        self.size = size  # 棋盘尺寸
        self.name = 'Game'     # 游戏的名称
        self.value_array = None     # 单元格合法的值的集合

    @staticmethod
    def is_wrong(data, conditions):  # 查错
        for rule in conditions:
            for item in conditions[rule]:
                if rule.is_wrong(data, item):
                    return True
        return False

    @staticmethod
    def print(puzzle, data):  # 打印数据
        pass

    @staticmethod
    def compile_puzzle(puzzle):   # 编译题目
        return {}

    def get_answer(self, puzzle, count=1):    # 根据题目数据求解答案，count为期望找到的答案数量
        buffer = []
        compiled_puzzle = self.compile_puzzle(puzzle)   # 先编译题目，让data知道该忽略那些单元格
        init_data = puzzle['init'] if 'init' in puzzle else None
        data = Data(self.size, self.value_array, init_data)
        if hasattr(self, 'ignore_cells'):   # 如果有需要忽略的单元格，先初始化，以后不再计算
            for index in self.ignore_cells:
                data.cells[index].values = {'.'}
        self._get_answer_(buffer, data, compiled_puzzle, count)
        # 解出的答案放在buffer列表中，如果列表为空表示无解
        return buffer

    def _get_answer_(self, answer_buffer, data, conditions, answer_count=1):
        # 如果期望数answer_count为零，则找到所有解
        # 如果已经找到期望数量的答案，不再计算，返回
        if answer_count != 0 and len(answer_buffer) >= answer_count:
            return
        try:
            # 循环计算，直至数据无变化
            total_length = data.total_length()
            while True:
                # 调用计算函数
                for rule in conditions:
                    for item in conditions[rule]:
                        rule.calculate(data, item)
                        # 如果此条件已完成，删掉???
                    # for index in range(len(conditions[rule])):
                    #     item = conditions[rule][index]
                    #     rule.calculate(data, item)
                    #     if rule.is_done(data, item):
                    #         conditions[rule][index] = None
                    # while None in conditions[rule]:
                    #     index = conditions[rule].index(None)
                    #     conditions[rule].pop(index)
                # 如果数据无变化，不再循环执行
                if data.total_length() == total_length:
                    break
                total_length = data.total_length()
            # 如果出错，放弃继续计算，返回
            # self.print({}, data)
            if self.is_wrong(data, conditions):
                return
            # 如果已完成，将答案添加到buffer中，返回
            if data.is_finish():
                answer_buffer.append(data)
                return

            # 以下是猜测部分，找个未完成单元格，遍历values
            # self.print({}, data)      # ..................................
            # print('guessing................................')
            index = data.get_undone_cell()
            # 此处打乱了遍历的顺序，给随机生成答案提供方便
            values = list(data.cells[index].values)
            # shuffle(values)
            for value in values:
                new_data = data.copy()
                new_data.cells[index].set_value(value)
                self._get_answer_(answer_buffer, new_data, conditions, answer_count)
        except FlyGameException:
            return

    def test(self, puzzle, count=1):     # 求解测试函数
        start_clock = clock()
        answers = self.get_answer(puzzle, count)
        for answer in answers:
            self.print(puzzle, answer)
        if len(answers) > 1:
            print('此题有多解，请审阅题目！')
        print('求解完毕，用时：{:.3f}秒。'.format(clock() - start_clock))
