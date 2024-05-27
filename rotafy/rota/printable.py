import datetime
import pandas
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import rota


class PrintableRota(rota.Rota):
    def __init__(self, name: str) -> None:
        super().__init__(name)
    
    
    def _ordinal(self, n: int) -> str:
        return f"{n:d}{'tsnrhtdd'[(n//10%10!=1)*(n%10<4)*n%10::4]}"
    
    def _human_readable_date(
            self, 
            date: datetime.date, 
            include_day_of_week: bool = False,
            include_year: bool = True
        ) -> str:
        date_ordinal = self._ordinal(date.day)
        
        format = f"{date_ordinal} %B"
        if include_day_of_week:
            format = "%A " + format
        
        if include_year:
            format += " %Y"
        
        human_readable = date.strftime(format)
        return human_readable
    
    
    def _draw_table_figure(self) -> matplotlib.figure.Figure:
        df_separate = self.dataframe.copy()
        width = len(df_separate.columns)
        height = df_separate.shape[0]
        if height == 0:
            raise Warning("There is no data to draw.")
            return None
        
        banding_light = (1, 1, 1) # white
        banding_dark = (0.965, 0.965, 0.965) # primary gray
        heading_colour = (0.083, 0.203, 0.273) # primary blue
        
        row_banding = [
            [[banding_light, banding_dark][i % 2]] * width
            for i in range(height)
        ]
        
        plt.rcParams["font.family"] = "Inter,sans-serif"
        plt.rcParams["font.size"] = 11
        fig, ax = plt.subplots()
        ax.axis("tight")
        ax.axis("off")
        
        table = ax.table(
            cellText=df_separate.values,
            cellLoc="center",
            cellColours=row_banding,
            rowLabels=df_separate.index,
            rowLoc="right",
            rowColours=[heading_colour] * height,
            colLabels=df_separate.columns,
            colColours=[heading_colour] * width,
            colLoc="center",
            loc="center"
        )
        
        for c in range(width):
            table[0, c].get_text().set_color(banding_dark)
        
        for r in range(height):
            table[r + 1, -1].get_text().set_color(banding_dark)
        
        return fig
    
    def pdf(self, output_file: str) -> None:
        with PdfPages(output_file) as pdf:
            fig = self._draw_table_figure()
            if fig is not None:
                pdf.savefig(fig, bbox_inches="tight")
            
            plt.close()
    
    def __str__(self) -> str:
        return self.dataframe.to_string()
    
    def print(self) -> None:
        print(self.__str__())
    
    
    @property
    def dataframe(self) -> pandas.DataFrame:
        all_chores = set(
            assignment.chore for row in self.rows for assignment in row
        )
        ordered_chores = list(all_chores)
        ordered_chores.sort(key=lambda c: c.ordinal)
        self.sort()
        
        data = {
            row.date: [row[chore.name] for chore in ordered_chores]
            for row in self.rows
        }
        df = pandas.Dataframe.from_dict(
            data,
            orient="index", 
            columns=ordered_chores
        )
        start_of_today = datetime.datetime.combine(
            datetime.datetime.today(), 
            datetime.time.min
        )
        min_ts = pandas.Timestamp(start_of_today)
        df = df[df.index >= min_ts]
        df.index = df.index.map(self._human_readable_date)
        df.fillna("-", inplace=True)
        return df