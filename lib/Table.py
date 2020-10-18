
#!/usr/bin/env python

# Author: Will Stevens (CloudOps) - wstevens@cloudops.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class TableRST(object):
    """
    Creates a new RST text based table.
    table = TableRST([
        ("<col_heading_1>", <col_width_1>),
        ("<col_heading_2>", <col_width_2>),
        ...
    ])
    """
    
    def __init__(self, cols=[]):
        self.titles = []
        self.widths = []
        self.table = """"""
        for c in cols:
            if len(c) == 2:
                if isinstance(c[0], str) and isinstance(c[1], int):
                    self.titles.append(c[0])
                    if len(c[0]) + 2 > c[1]:
                        self.widths.append(len(c[0]) + 2)
                    else:
                        self.widths.append(c[1])
                else:
                    raise IOError('Table column intialization must be of the form \'(string, int)\'.')
            else:
                raise IOError('Malformed Table initialization.')
    
        # add the table header
        for i, w in enumerate(self.widths):
            if i == 0:
                self.table += '+'
            self.table += '-'*w + '+'
        self.table += '\n'
        for i, w in enumerate(self.widths):
            self.table += ('| %s' % self.titles[i]).ljust(w + 1)
            if i == len(self.widths) - 1:
                self.table += '|'
        self.table += '\n'
        for i, w in enumerate(self.widths):
            if i == 0:
                self.table += '+'
            self.table += '='*w + '+'
        self.table += '\n'


    def add_row(self, row=[]):
        """
        Add a row to the table.  The length of 'row' must be the same as Table initialization.
        """
        if len(row) != len(self.titles):
            raise IOError('Each row must have the same length as the constructed table.')

        splitter = [[]] * len(row) # creates: [[], [], [], ...]
        for i, content in enumerate(row):
            splitter[i] = content.split(' ')

        # before we output anything, make sure we can...
        for i, split in enumerate(splitter):
            for word in split:
                if len(word) > self.widths[i] - 2:
                    raise IOError('The word \'%s\' in column \'%s\' is longer than the column width (%s chars).' % (
                        word, self.titles[i], self.widths[i]
                    ))

        finished = False
        while not finished:
            for i, split in enumerate(splitter):
                temp = ''
                words_to_remove = 0
                has_newline = False
                for w, word in enumerate(split):
                    has_newline = False
                    after_newline = ''
                    if '\n' in word: # handle new lines in the content
                        has_newline = True
                        lines = word.split('\n')
                        if len(lines) >= 2:
                            word = lines[0]
                            after_newline = '\n'.join(lines[1:])
                    if (len(temp) > 0 and len(temp) + len(word) + 1 <= self.widths[i] - 2) or (
                        len(temp) == 0 and len(word) <= self.widths[i] - 2): # fits on current line
                        
                        if len(temp) > 0: # only add a blank line if there are words in temp
                            temp += ' '
                        temp += word

                        if has_newline:
                            splitter[i] = [after_newline] + split[w+1:]
                            break
                        else:
                            words_to_remove += 1
                    else: # handle wrapping the current word to the next line
                        splitter[i] = split[w:] # update the splitter array to include only remaining items
                        break
                # print temp as this is either the last line with text or is an empty line
                self.table += ('| %s' % temp).ljust(self.widths[i] + 1) # content of this column
                if not has_newline:
                    splitter[i] = split[words_to_remove:]
                if i == len(splitter) - 1: # add trailing pipe and newline
                    self.table += '|\n'

            # check if we have finished printing everything
            finished = True
            for l in splitter:
                if len(l) > 0:
                    finished = False

        # print the bottom of the row
        for i, w in enumerate(self.widths):
            if i == 0:
                self.table += '+'
            self.table += '-'*w + '+'
        self.table += '\n'


    def draw(self):
        """
        Return the formatted table.
        """
        return self.table.encode('utf-8')




class TableMD(object):
    """
    Creates a new MD text based table.
    table = TableMD(["<col_heading_1>", "<col_heading_2>", ...])
    """
    
    def __init__(self, cols=[]):
        # add the table header
        self.table = """"""
        self.table += ' | '.join(cols)
        self.table += '\n'
        self.table += ' | '.join(['---' for c in cols])
        self.table += '\n'


    def add_row(self, row=[]):
        """
        Add a row to the table.
        """
        self.table += ' | '.join([r for r in row])
        self.table += '\n'


    def draw(self):
        """
        Return the formatted table.
        """
        return self.table.encode('utf-8')
