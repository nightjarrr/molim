import check
import pathlib
import processing
import sh


class FfmpegNotFoundError(Exception):
    DEFAULT_MESSAGE = "Could not run ffmpeg command. Check whether FFMpeg is installed on your system and is available on PATH."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


class FfmpegRuntimeError(Exception):
    DEFAULT_MESSAGE = (
        "An error occurred during FFMpeg execution. ffmpeg exit code: {exit_code}"
    )

    def __init__(self, internal_error: sh.ErrorReturnCode):
        self.message = FfmpegRuntimeError.DEFAULT_MESSAGE.format(
            exit_code=internal_error.exit_code
        )
        self.internal_error = internal_error
        super().__init__(self.message)

    def __repr__(self):
        return f'{self.__class__.__name__}(message="{self.message}", internal_error={repr(self.internal_error)})'


class FfmpegFileProcessor(processing.FileProcessor):
    def __init__(
        self,
        ffmpeg_codec: str,
        ffmpeg_rate: int,
        ffmpeg_additional: str,
        ffmpeg_report: bool,
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(output_strategy, post_processor)
        check.ensure_type(ffmpeg_codec, str)
        check.ensure_int_between(ffmpeg_rate, 0, 51)
        if ffmpeg_additional is not None:
            check.ensure_type(ffmpeg_additional, str)
        check.ensure_type(ffmpeg_report, bool)
        self.__ffmpeg_codec = ffmpeg_codec
        self.__ffmpeg_rate = ffmpeg_rate
        self.__ffmpeg_additional = ffmpeg_additional
        self.__ffmpeg_report = ffmpeg_report
        try:
            # This will fail if there's no ffmpeg command available.
            self.__ffmpeg = sh.ffmpeg
        except sh.CommandNotFound:
            raise FfmpegNotFoundError()
        try:
            # Run 'ffmpeg -version' to ensure that it is able to launch successfully.
            self.__ffmpeg("-version")
        except sh.ErrorReturnCode as e:
            raise FfmpegRuntimeError(e)
        self.__args = []

    def _prepare_execution(
        self, file_path: pathlib.Path, output_file_path: pathlib.Path
    ) -> None:
        self.__args = [
            "-y",
            "-i",
            str(file_path),  # Input
            "-vcodec",
            self.__ffmpeg_codec,  # Codec
            "-crf",
            str(self.__ffmpeg_rate),
        ]
        if self.__ffmpeg_additional:
            addl = self.__ffmpeg_additional.split(" ")
            self.__args += addl
        self.__args.append(f"{output_file_path}")  # Output
        if self.__ffmpeg_report:
            self.__args.append("-report")

        print(" ".join(self.__args))

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        try:
            # ffmpeg -i "$fullpath" -vcodec libx265 -crf 26 "$newpath"
            self.__ffmpeg(*self.__args)
        except sh.ErrorReturnCode as e:
            raise FfmpegRuntimeError(e)
